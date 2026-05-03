"""Phase 2: 임베딩 + 카테고리 태깅 + 클러스터링.

파이프라인:
1. 각 레포의 임베딩용 텍스트 생성 (description+topics+README+의존성 키워드)
2. Ollama bge-m3로 임베딩 → analysis.embedding (BLOB)
3. Ollama qwen2.5:14b로 도메인/형태/상태 분류 → analysis.{domain,form,status}
4. UMAP(2D) → KMeans(k=6) 클러스터링 → analysis.cluster_id
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from .config import config
from .llm import OllamaClient, EMBED_MODEL, TAG_MODEL, USER_CONTEXT
from .models import Analysis, Repo, get_session, init_db

console = Console()

DOMAINS = ["임상AI", "풀스택웹앱", "인프라도구", "학습용", "취미", "기타"]
FORMS = ["웹앱", "CLI", "라이브러리", "PWA", "노트북", "기타"]
STATUSES = ["active", "archived", "abandoned"]

# 임베딩 입력 길이 제한 (bge-m3 max 8192 token, 안전하게 4000자)
EMBED_TEXT_MAX = 4000
README_HEAD_LEN = 2000


def build_embed_text(repo: Repo) -> str:
    """레포 1개의 임베딩 입력 텍스트 구성."""
    parts: list[str] = []
    if repo.description:
        parts.append(f"설명: {repo.description}")
    if repo.topics:
        parts.append(f"토픽: {', '.join(repo.topics)}")
    if repo.language:
        parts.append(f"언어: {repo.language}")

    # 주요 의존성 키워드
    if repo.package_files:
        dep_keys = list(repo.package_files.keys())
        parts.append(f"의존성파일: {', '.join(dep_keys)}")

    # README 앞부분
    if repo.readme:
        parts.append(f"README:\n{repo.readme[:README_HEAD_LEN]}")

    text = "\n".join(parts)
    return text[:EMBED_TEXT_MAX]


def determine_status(repo: Repo) -> str:
    """마지막 push + README 유무로 상태 휴리스틱 결정.
    - active: 최근 90일 이내 push
    - archived: GitHub archived 플래그
    - abandoned: 1년 이상 push 없음 또는 README 없음
    """
    if repo.is_archived:
        return "archived"
    if not repo.pushed_at:
        return "abandoned"
    days = (datetime.utcnow() - repo.pushed_at.replace(tzinfo=None)).days
    if days <= 90:
        return "active"
    if days >= 365:
        return "abandoned"
    return "active"


def tag_repo(client: OllamaClient, repo: Repo) -> dict[str, str]:
    """로컬 LLM으로 도메인/형태 분류."""
    embed_text_short = build_embed_text(repo)[:1500]

    system = USER_CONTEXT + (
        "\n위 사용자가 만든 GitHub 레포를 분류한다. JSON으로만 답한다."
    )
    prompt = f"""다음 레포를 분류해줘:

{embed_text_short}

다음 JSON 스키마로만 답해 (키 외 다른 텍스트 금지):
{{
  "domain": "{' | '.join(DOMAINS)}",
  "form": "{' | '.join(FORMS)}"
}}
"""
    result = client.chat_json(prompt, model=TAG_MODEL, system=system)
    domain = result.get("domain", "기타")
    form = result.get("form", "기타")
    if domain not in DOMAINS:
        domain = "기타"
    if form not in FORMS:
        form = "기타"
    return {"domain": domain, "form": form}


def array_to_blob(arr: np.ndarray) -> bytes:
    """numpy → bytes (float32로 통일)."""
    return arr.astype(np.float32).tobytes()


def blob_to_array(blob: bytes) -> np.ndarray:
    return np.frombuffer(blob, dtype=np.float32)


def upsert_analysis(
    session,
    repo_id: int,
    *,
    domain: str | None = None,
    form: str | None = None,
    status: str | None = None,
    embedding: bytes | None = None,
    cluster_id: int | None = None,
) -> None:
    """analysis upsert. None이면 기존 값 유지."""
    a = session.query(Analysis).filter_by(repo_id=repo_id).first()
    if a is None:
        a = Analysis(repo_id=repo_id)
        session.add(a)
    if domain is not None:
        a.domain = domain
    if form is not None:
        a.form = form
    if status is not None:
        a.status = status
    if embedding is not None:
        a.embedding = embedding
    if cluster_id is not None:
        a.cluster_id = cluster_id
    a.analyzed_at = datetime.utcnow()


def cluster_repos(
    embeddings: np.ndarray, k: int = 6
) -> tuple[np.ndarray, np.ndarray]:
    """UMAP(2D) + KMeans. 작은 N에 안정적."""
    from sklearn.cluster import KMeans
    import umap

    n = embeddings.shape[0]
    k_eff = min(k, max(2, n // 3))  # 너무 작은 N 방어

    reducer = umap.UMAP(
        n_components=2,
        n_neighbors=min(15, n - 1),
        min_dist=0.1,
        random_state=42,
        metric="cosine",
    )
    coords_2d = reducer.fit_transform(embeddings)

    kmeans = KMeans(n_clusters=k_eff, random_state=42, n_init=10)
    labels = kmeans.fit_predict(coords_2d)

    return coords_2d, labels


def run_analyze(*, rerun: bool = False, k: int = 6) -> dict[str, int]:
    """전체 Phase 2 파이프라인."""
    config.validate()
    init_db()

    client = OllamaClient()
    if not client.health():
        raise RuntimeError(
            f"Ollama 서버 응답 없음 ({client.host}). "
            "Ollama 데스크톱 앱이 실행 중인지 확인하세요."
        )
    if not client.has_model(EMBED_MODEL):
        raise RuntimeError(
            f"Ollama 모델 '{EMBED_MODEL}' 미설치. `ollama pull {EMBED_MODEL}` 실행."
        )
    if not client.has_model(TAG_MODEL):
        raise RuntimeError(
            f"Ollama 모델 '{TAG_MODEL}' 미설치. `ollama pull {TAG_MODEL}` 실행."
        )

    session = get_session()
    counts = {"embedded": 0, "tagged": 0, "clustered": 0, "skipped": 0}

    try:
        repos: list[Repo] = session.query(Repo).all()
        if not repos:
            console.print(
                "[yellow]저장된 레포가 없습니다. 먼저 [cyan]vibe collect[/cyan].[/yellow]"
            )
            return counts

        console.print(f"[cyan]대상 레포: {len(repos)}개[/cyan]")

        # === Step 1+2: 임베딩 + 태깅 ===
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total}"),
            console=console,
        ) as progress:
            task = progress.add_task("임베딩 + 카테고리 태깅", total=len(repos))

            for repo in repos:
                existing = (
                    session.query(Analysis).filter_by(repo_id=repo.id).first()
                )
                if existing and existing.embedding and not rerun:
                    counts["skipped"] += 1
                    progress.update(task, advance=1)
                    continue

                # 임베딩
                text = build_embed_text(repo)
                if not text.strip():
                    text = repo.name  # 최소한 이름이라도
                vec = client.embed(text, model=EMBED_MODEL)
                emb_blob = array_to_blob(np.asarray(vec, dtype=np.float32))

                # 카테고리
                tags = tag_repo(client, repo)
                status = determine_status(repo)

                upsert_analysis(
                    session,
                    repo_id=repo.id,
                    domain=tags["domain"],
                    form=tags["form"],
                    status=status,
                    embedding=emb_blob,
                )
                counts["embedded"] += 1
                counts["tagged"] += 1
                session.commit()
                progress.update(task, advance=1)

        # === Step 3: 클러스터링 ===
        analyses = (
            session.query(Analysis).filter(Analysis.embedding.isnot(None)).all()
        )
        if len(analyses) < 4:
            console.print(
                f"[yellow]임베딩된 레포가 {len(analyses)}개뿐. 클러스터링 스킵.[/yellow]"
            )
            return counts

        embs = np.stack([blob_to_array(a.embedding) for a in analyses])
        console.print(
            f"[cyan]UMAP(2D) + KMeans(k={min(k, max(2, len(analyses)//3))}) 실행 중...[/cyan]"
        )
        _coords, labels = cluster_repos(embs, k=k)

        for a, label in zip(analyses, labels):
            a.cluster_id = int(label)
        session.commit()
        counts["clustered"] = len(analyses)

        console.print(
            f"[bold green]✓ 임베딩 {counts['embedded']} / 태깅 {counts['tagged']} / "
            f"클러스터 {counts['clustered']} / 스킵 {counts['skipped']}[/bold green]"
        )
        return counts

    finally:
        session.close()


def show_clusters() -> None:
    """클러스터별 레포 목록 출력."""
    from rich.table import Table

    init_db()
    session = get_session()
    try:
        analyses = (
            session.query(Analysis)
            .filter(Analysis.cluster_id.isnot(None))
            .all()
        )
        if not analyses:
            console.print(
                "[yellow]클러스터링 결과 없음. 먼저 [cyan]vibe analyze[/cyan].[/yellow]"
            )
            return

        # cluster_id별 그룹화
        by_cluster: dict[int, list[Analysis]] = {}
        for a in analyses:
            by_cluster.setdefault(a.cluster_id, []).append(a)

        for cid in sorted(by_cluster.keys()):
            members = by_cluster[cid]
            table = Table(
                title=f"\nCluster {cid} ({len(members)}개)",
                show_header=True,
                header_style="bold magenta",
            )
            table.add_column("레포", style="cyan")
            table.add_column("도메인")
            table.add_column("형태")
            table.add_column("상태")
            table.add_column("언어")

            for a in sorted(members, key=lambda x: x.repo.name.lower()):
                table.add_row(
                    a.repo.name,
                    a.domain or "-",
                    a.form or "-",
                    a.status or "-",
                    a.repo.language or "-",
                )
            console.print(table)
    finally:
        session.close()
