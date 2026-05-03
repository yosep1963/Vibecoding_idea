"""Phase 1: GitHub 레포 메타데이터 + README + 의존성 파일 수집."""
from __future__ import annotations

import asyncio
import base64
from datetime import datetime
from typing import Any

import httpx
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from .config import config
from .models import Repo, init_db, get_session

console = Console()

GITHUB_API = "https://api.github.com"
DEPENDENCY_FILES = [
    "package.json",
    "requirements.txt",
    "pyproject.toml",
    "Cargo.toml",
    "go.mod",
    "build.gradle",
    "pom.xml",
    "CLAUDE.md",  # 본인이 vibe coding 자주 하니까 이것도 수집
]


class GitHubClient:
    """비동기 GitHub API 클라이언트."""

    def __init__(self, token: str, username: str):
        self.username = username
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        self.client = httpx.AsyncClient(
            headers=self.headers,
            timeout=30.0,
            limits=httpx.Limits(max_connections=10),
        )

    async def close(self) -> None:
        await self.client.aclose()

    async def list_repos(self) -> list[dict[str, Any]]:
        """본인이 소유한 모든 레포 목록 (페이지네이션 처리)."""
        repos: list[dict[str, Any]] = []
        page = 1
        per_page = 100

        while True:
            resp = await self._request(
                "GET",
                f"/user/repos",
                params={
                    "per_page": per_page,
                    "page": page,
                    "type": "owner",  # 본인 소유만
                    "sort": "pushed",
                },
            )
            batch = resp.json()
            if not batch:
                break
            repos.extend(batch)
            if len(batch) < per_page:
                break
            page += 1

        return repos

    async def get_readme(self, full_name: str) -> str | None:
        """README 가져오기. 없으면 None."""
        try:
            resp = await self._request("GET", f"/repos/{full_name}/readme")
            if resp.status_code == 404:
                return None
            data = resp.json()
            content_b64 = data.get("content", "")
            if not content_b64:
                return None
            return base64.b64decode(content_b64).decode("utf-8", errors="replace")
        except httpx.HTTPStatusError:
            return None

    async def get_file(self, full_name: str, path: str) -> str | None:
        """특정 파일 내용 가져오기. 없으면 None."""
        try:
            resp = await self._request(
                "GET", f"/repos/{full_name}/contents/{path}"
            )
            if resp.status_code == 404:
                return None
            data = resp.json()
            if isinstance(data, list):  # 디렉토리인 경우
                return None
            content_b64 = data.get("content", "")
            if not content_b64:
                return None
            return base64.b64decode(content_b64).decode("utf-8", errors="replace")
        except httpx.HTTPStatusError:
            return None

    async def _request(
        self, method: str, path: str, **kwargs
    ) -> httpx.Response:
        """레이트 리밋 대비 retry 로직 포함."""
        url = f"{GITHUB_API}{path}"
        for attempt in range(3):
            resp = await self.client.request(method, url, **kwargs)

            # rate limit 처리
            if resp.status_code == 403 and "rate limit" in resp.text.lower():
                reset = int(resp.headers.get("X-RateLimit-Reset", "0"))
                wait = max(reset - int(datetime.utcnow().timestamp()), 1)
                console.print(
                    f"[yellow]Rate limit. {wait}초 대기...[/yellow]"
                )
                await asyncio.sleep(min(wait, 60))
                continue

            # 404는 정상 (파일 없음)
            if resp.status_code == 404:
                return resp

            resp.raise_for_status()
            return resp

        raise RuntimeError(f"3회 재시도 후 실패: {url}")


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


async def collect_dependency_files(
    client: GitHubClient, full_name: str
) -> dict[str, str]:
    """의존성 파일들 병렬 수집."""
    tasks = [client.get_file(full_name, fname) for fname in DEPENDENCY_FILES]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    out: dict[str, str] = {}
    for fname, content in zip(DEPENDENCY_FILES, results):
        if isinstance(content, Exception):
            continue
        if content:
            # 너무 긴 파일은 잘라서 저장 (분석에 충분한 양만)
            out[fname] = content[:5000]
    return out


async def collect_one_repo(
    client: GitHubClient, repo_data: dict[str, Any]
) -> dict[str, Any]:
    """레포 하나의 README + 의존성 파일 수집."""
    full_name = repo_data["full_name"]

    readme_task = client.get_readme(full_name)
    deps_task = collect_dependency_files(client, full_name)

    readme, deps = await asyncio.gather(readme_task, deps_task)

    return {
        "name": repo_data["name"],
        "full_name": full_name,
        "description": repo_data.get("description"),
        "language": repo_data.get("language"),
        "topics": repo_data.get("topics", []),
        "stars": repo_data.get("stargazers_count", 0),
        "forks": repo_data.get("forks_count", 0),
        "is_fork": int(repo_data.get("fork", False)),
        "is_archived": int(repo_data.get("archived", False)),
        "created_at": _parse_dt(repo_data.get("created_at")),
        "pushed_at": _parse_dt(repo_data.get("pushed_at")),
        "readme": readme[:20000] if readme else None,  # 너무 긴 README 자르기
        "package_files": deps,
    }


def save_repos(rows: list[dict[str, Any]]) -> int:
    """SQLite에 upsert. 이미 있는 레포는 업데이트."""
    session = get_session()
    saved = 0
    try:
        for row in rows:
            existing = session.query(Repo).filter_by(name=row["name"]).first()
            if existing:
                for key, value in row.items():
                    setattr(existing, key, value)
                existing.fetched_at = datetime.utcnow()
            else:
                session.add(Repo(**row, fetched_at=datetime.utcnow()))
            saved += 1
        session.commit()
    finally:
        session.close()
    return saved


async def collect_all(
    *, skip_forks: bool = True, skip_archived: bool = False
) -> int:
    """엔트리 포인트: 모든 레포 수집 → DB 저장."""
    config.validate()
    init_db()

    client = GitHubClient(config.GITHUB_TOKEN, config.GITHUB_USERNAME)
    try:
        console.print(f"[cyan]GitHub 레포 목록 가져오는 중...[/cyan]")
        all_repos = await client.list_repos()

        # 필터링
        repos = [
            r for r in all_repos
            if not (skip_forks and r.get("fork"))
            and not (skip_archived and r.get("archived"))
        ]

        console.print(
            f"[green]전체 {len(all_repos)}개 중 분석 대상: {len(repos)}개[/green]"
        )

        # 진행률 표시하며 수집
        rows: list[dict[str, Any]] = []
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total}"),
            console=console,
        ) as progress:
            task = progress.add_task("README + deps 수집", total=len(repos))

            # 동시성 제한 (GitHub rate limit 보호)
            semaphore = asyncio.Semaphore(5)

            async def bounded(repo_data):
                async with semaphore:
                    result = await collect_one_repo(client, repo_data)
                    progress.update(task, advance=1)
                    return result

            rows = await asyncio.gather(*[bounded(r) for r in repos])

        # 저장
        saved = save_repos(rows)
        console.print(f"[bold green]✓ {saved}개 레포 저장 완료[/bold green]")
        console.print(f"[dim]DB 위치: {config.DB_PATH}[/dim]")
        return saved

    finally:
        await client.close()
