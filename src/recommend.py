"""Phase 3: 빈틈 분석 + Claude Agent SDK로 다음 프로젝트 3개 추천 + CLAUDE.md 초안 생성.

설계 원칙:
- 빈틈 분석은 로컬에서 수행 (도메인×형태 매트릭스, 클러스터 통계)
- Claude에는 요약본만 전달 (전체 README 보내지 않음 — 보안 + 토큰 절약)
- 출력 형식 강제: JSON Schema (claude-agent-sdk output_format)
- 인증: Claude Code Pro/Max 구독 OAuth (별도 API 키 불필요)
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import anyio
from claude_agent_sdk import (
    ClaudeAgentOptions,
    ResultMessage,
    query,
)
from rich.console import Console

from .analyze import DOMAINS, FORMS
from .config import ROOT, config
from .llm import USER_CONTEXT
from .models import Analysis, Recommendation, Repo, get_session, init_db

console = Console()

# Sonnet 4.6 — 추천 품질이 결정적이므로 여기서만 사용
RECOMMEND_MODEL = "claude-sonnet-4-6"
OUTPUT_DIR = ROOT / "output"

# JSON Schema — Claude 응답을 강제 검증
RECOMMENDATION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "recommendations": {
            "type": "array",
            "minItems": 3,
            "maxItems": 3,
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "maxLength": 25},
                    "summary": {"type": "string", "maxLength": 80},
                    "domain": {
                        "type": "string",
                        "enum": ["임상AI", "풀스택웹앱", "인프라도구", "학습용", "취미"],
                    },
                    "form": {
                        "type": "string",
                        "enum": ["웹앱", "CLI", "라이브러리", "PWA", "노트북"],
                    },
                    "duration": {
                        "type": "string",
                        "enum": ["주말", "1-2주", "1개월+"],
                    },
                    "reuse": {"type": "string"},
                    "learn": {"type": "string"},
                    "why": {"type": "string"},
                    "first_steps": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 3,
                        "maxItems": 3,
                    },
                },
                "required": [
                    "title", "summary", "domain", "form", "duration",
                    "reuse", "learn", "why", "first_steps",
                ],
            },
        },
    },
    "required": ["recommendations"],
}


def build_repo_summary(repos_with_analysis: list[tuple[Repo, Analysis]]) -> dict[str, Any]:
    """Claude에게 보낼 요약 데이터 구성. README 본문 미포함."""
    # 도메인×형태 매트릭스
    matrix: dict[tuple[str, str], int] = {}
    for _, a in repos_with_analysis:
        if a.domain and a.form:
            matrix[(a.domain, a.form)] = matrix.get((a.domain, a.form), 0) + 1

    # 빈 영역 (의대 교수 컨텍스트에서 의미있을 만한 조합만)
    meaningful_combos = [
        (d, f) for d in DOMAINS for f in FORMS
        if d != "기타" and f != "기타"
    ]
    empty_combos = [c for c in meaningful_combos if matrix.get(c, 0) == 0]
    sparse_combos = [
        (c, matrix[c]) for c in meaningful_combos if 0 < matrix.get(c, 0) <= 1
    ]

    # 클러스터 통계
    cluster_groups: dict[int, list[str]] = {}
    for r, a in repos_with_analysis:
        if a.cluster_id is not None:
            cluster_groups.setdefault(a.cluster_id, []).append(r.name)

    # 레포 간단 인벤토리 (이름 + 1줄 설명 + 도메인/형태)
    inventory = []
    for r, a in repos_with_analysis:
        inventory.append({
            "name": r.name,
            "lang": r.language or "-",
            "domain": a.domain or "-",
            "form": a.form or "-",
            "desc": (r.description or "")[:120],
            "topics": r.topics or [],
            "pushed": r.pushed_at.strftime("%Y-%m") if r.pushed_at else "-",
            "deps": list(r.package_files.keys()) if r.package_files else [],
        })

    return {
        "total_repos": len(repos_with_analysis),
        "domain_form_matrix": {f"{d}|{f}": n for (d, f), n in matrix.items()},
        "empty_combinations": [f"{d}+{f}" for d, f in empty_combos],
        "sparse_combinations": [f"{d}+{f} ({n}개)" for (d, f), n in sparse_combos],
        "clusters": {
            f"cluster_{cid}": names for cid, names in cluster_groups.items()
        },
        "inventory": inventory,
    }


def build_prompt(summary: dict[str, Any]) -> str:
    """추천 프롬프트. 뻔한 추천 명시적 배제 + 출력 형식 강제."""
    return f"""다음은 사용자의 GitHub 활동 데이터다 (총 {summary['total_repos']}개 레포).

## 도메인 × 형태 매트릭스 (현재 분포)
{json.dumps(summary['domain_form_matrix'], ensure_ascii=False, indent=2)}

## 비어있는 의미있는 조합 (만들 법한데 안 만든 영역)
{json.dumps(summary['empty_combinations'], ensure_ascii=False, indent=2)}

## 단 1개만 있는 sparse 조합
{json.dumps(summary['sparse_combinations'], ensure_ascii=False, indent=2)}

## 클러스터 (UMAP+KMeans 결과)
{json.dumps(summary['clusters'], ensure_ascii=False, indent=2)}

## 레포 인벤토리 (요약)
{json.dumps(summary['inventory'], ensure_ascii=False, indent=2)}

---

위 패턴을 보고, **다음에 만들 법한데 아직 안 만든 프로젝트 3개**를 추천해줘.

**금지 사항:**
- 뻔한 추천 금지: Todo 앱, 블로그, 일반 포트폴리오 사이트, "AI 챗봇", weather app 등
- 이미 비슷한 게 인벤토리에 있는 건 추천 금지 (FIB4, MELD, SOFA류 단일 계산기 새로 추천 X)
- "이런 거 만들어 보세요" 류 일반론 금지

**필수 반영:**
- 사용자 컨텍스트 (소화기내과 간장학 교수 + 임상 30년차 + 임상 AI 연구) 무시 금지
- 본인의 빈틈 데이터 (위 empty/sparse/cluster) 활용
- 기존 레포의 자산 재활용을 명시 (어느 레포의 어느 부분?)

**각 추천은 다음 JSON 구조로:**
```json
{{
  "recommendations": [
    {{
      "title": "프로젝트 이름 (영문, 25자 이내)",
      "summary": "한 줄 요약 (한국어, 80자 이내)",
      "domain": "임상AI | 풀스택웹앱 | 인프라도구 | 학습용 | 취미",
      "form": "웹앱 | CLI | 라이브러리 | PWA | 노트북",
      "duration": "주말 | 1-2주 | 1개월+",
      "reuse": "어느 레포의 어느 부분을 재활용 (구체적으로)",
      "learn": "새로 배워야 할 것 1-2개 (구체적으로)",
      "why": "왜 이 사용자에게 의미있는가 (간장학+임상 컨텍스트에서)",
      "first_steps": ["첫 PR 1", "첫 PR 2", "첫 PR 3"]
    }},
    ...
  ]
}}
```

JSON만 출력. 다른 설명 텍스트 금지.
"""


def build_claude_md(rec: dict[str, Any]) -> str:
    """추천 1개 → CLAUDE.md 초안."""
    title = rec.get("title", "Project")
    return f"""# CLAUDE.md

> {title} — Vibe Idea Generator가 생성한 초기 컨텍스트.

## 프로젝트

**{title}** — {rec.get('summary', '')}

## 사용자 컨텍스트 (모든 LLM 호출에 주입)

- 직업: 대구가톨릭대학교 의과대학 소화기내과 교수 (간장학)
- 임상 30년차, 2028년 8월 정년
- 개발 스타일: Vibe coding, 임상 AI + 풀스택 웹앱이 주력
- 한국어 응답 선호

## 분류

- 도메인: {rec.get('domain', '-')}
- 형태: {rec.get('form', '-')}
- 예상 소요: {rec.get('duration', '-')}

## 재사용 자산

{rec.get('reuse', '-')}

## 새로 배울 것

{rec.get('learn', '-')}

## 왜 의미있는가

{rec.get('why', '-')}

## 첫 PR 단계

{chr(10).join(f"{i+1}. {s}" for i, s in enumerate(rec.get('first_steps', [])))}

## 기술 스택 (제안)

> Vibe Idea Gen이 추천한 형태({rec.get('form')})에 맞춰 사용자가 직접 결정.
> 기존 레포의 패턴 참고할 것.

## 코딩 규약

- 경로: `pathlib.Path` 필수 (Windows 호환)
- 한국어 주석 OK
- 작은 샘플로 먼저 테스트
"""


def safe_dirname(name: str) -> str:
    """Windows 파일명 안전화."""
    return re.sub(r'[<>:"/\\|?*\s]+', '_', name).strip('_')[:60]


async def _query_claude_async(prompt: str) -> tuple[dict[str, Any], float]:
    """claude-agent-sdk로 단발성 호출 → (structured_output, total_cost_usd)."""
    options = ClaudeAgentOptions(
        model=RECOMMEND_MODEL,
        system_prompt=USER_CONTEXT
        + "\n너는 위 사용자의 GitHub 활동 패턴을 분석하는 메타 도구다.",
        # output_format 사용 시 SDK가 내부 검증/재시도를 위해 2–3턴 소비.
        # max_turns=1은 "Reached maximum number of turns" 에러 → 여유 있게 5.
        max_turns=5,
        allowed_tools=[],  # 도구 사용 차단 → 순수 분석/응답만
        output_format={"type": "json_schema", "schema": RECOMMENDATION_SCHEMA},
    )
    structured: dict[str, Any] | None = None
    cost = 0.0
    async for msg in query(prompt=prompt, options=options):
        if isinstance(msg, ResultMessage):
            structured = getattr(msg, "structured_output", None)
            cost = getattr(msg, "total_cost_usd", 0.0) or 0.0
    if structured is None:
        raise RuntimeError(
            "Claude Agent SDK가 structured_output을 반환하지 않음. "
            "JSON Schema 검증 실패 가능. 프롬프트/스키마 확인 필요."
        )
    return structured, cost


def call_claude(prompt: str) -> dict[str, Any]:
    """동기 래퍼: claude-agent-sdk 호출 + 비용 표시."""
    result, cost = anyio.run(_query_claude_async, prompt)
    if cost > 0:
        console.print(
            f"[dim]API 호출 비용: ${cost:.4f} "
            f"(Claude Code 구독 한도 내라면 청구되지 않음)[/dim]"
        )
    return result


def run_recommend() -> dict[str, Any]:
    """Phase 3 전체 파이프라인."""
    config.validate(require_claude=True)
    init_db()

    session = get_session()
    try:
        repos_with_analysis = (
            session.query(Repo, Analysis)
            .join(Analysis, Repo.id == Analysis.repo_id)
            .all()
        )
        if not repos_with_analysis:
            raise RuntimeError(
                "분석된 레포가 없습니다. 먼저 vibe analyze 실행."
            )

        console.print(
            f"[cyan]대상 레포: {len(repos_with_analysis)}개. 빈틈 분석 중...[/cyan]"
        )
        summary = build_repo_summary(repos_with_analysis)

        console.print(
            f"[cyan]빈 조합: {len(summary['empty_combinations'])}개, "
            f"sparse: {len(summary['sparse_combinations'])}개[/cyan]"
        )
        console.print(
            f"[cyan]Claude Agent SDK ({RECOMMEND_MODEL}) 호출 중... "
            f"(구독 OAuth 사용)[/cyan]"
        )

        prompt = build_prompt(summary)
        result = call_claude(prompt)

        recs = result.get("recommendations", [])
        if not recs:
            raise RuntimeError(f"Claude가 빈 추천 반환: {result}")

        # DB 저장
        rec_row = Recommendation(
            generated_at=datetime.utcnow(),
            payload=result,
            acted_on=[],
        )
        session.add(rec_row)
        session.commit()
        rec_id = rec_row.id

        # CLAUDE.md 초안 생성
        OUTPUT_DIR.mkdir(exist_ok=True)
        for rec in recs:
            title = rec.get("title", "untitled")
            d = OUTPUT_DIR / safe_dirname(title)
            d.mkdir(exist_ok=True)
            (d / "CLAUDE.md").write_text(
                build_claude_md(rec), encoding="utf-8"
            )

        # 화면 출력
        console.print(
            f"\n[bold green]✓ 추천 {len(recs)}개 생성 완료 (rec_id={rec_id})[/bold green]"
        )
        for i, rec in enumerate(recs, 1):
            console.print(f"\n[bold cyan]── 추천 {i}: {rec.get('title')} ──[/bold cyan]")
            console.print(f"[bold]요약:[/bold] {rec.get('summary')}")
            console.print(
                f"[dim]도메인: {rec.get('domain')} | "
                f"형태: {rec.get('form')} | "
                f"소요: {rec.get('duration')}[/dim]"
            )
            console.print(f"[bold]재사용:[/bold] {rec.get('reuse')}")
            console.print(f"[bold]새로 배울 것:[/bold] {rec.get('learn')}")
            console.print(f"[bold]왜 의미있나:[/bold] {rec.get('why')}")
            steps = rec.get("first_steps", [])
            if steps:
                console.print("[bold]첫 PR 단계:[/bold]")
                for j, s in enumerate(steps, 1):
                    console.print(f"  {j}. {s}")

        console.print(
            f"\n[dim]CLAUDE.md 초안: {OUTPUT_DIR}\\<프로젝트명>\\CLAUDE.md[/dim]"
        )
        return result

    finally:
        session.close()


def show_recommend_history() -> None:
    """과거 추천 이력 + 실제로 시작한 항목(acted_on) 표시."""
    from rich.table import Table

    init_db()
    session = get_session()
    try:
        recs = (
            session.query(Recommendation)
            .order_by(Recommendation.generated_at.desc())
            .all()
        )
        if not recs:
            console.print(
                "[yellow]추천 이력 없음. 먼저 [cyan]vibe recommend[/cyan].[/yellow]"
            )
            return

        table = Table(
            title="추천 이력", show_header=True, header_style="bold magenta"
        )
        table.add_column("ID", justify="right")
        table.add_column("생성 시각")
        table.add_column("추천 제목들 (★ = 실제 시작)")

        total_recs = 0
        total_acted = 0
        for r in recs:
            titles = [
                rec.get("title", "?")
                for rec in (r.payload or {}).get("recommendations", [])
            ]
            acted = set(r.acted_on or [])
            marked = [
                f"[bold green]★ {t}[/bold green]" if t in acted else t
                for t in titles
            ]
            total_recs += len(titles)
            total_acted += len(acted)
            table.add_row(
                str(r.id),
                r.generated_at.strftime("%Y-%m-%d %H:%M"),
                ", ".join(marked),
            )
        console.print(table)
        if total_recs:
            ratio = total_acted / total_recs * 100
            console.print(
                f"\n[dim]실행률: {total_acted}/{total_recs} ({ratio:.0f}%). "
                f"[cyan]vibe acted <id> <title>[/cyan] 로 표시 추가[/dim]"
            )
    finally:
        session.close()


def _resolve_title(rec_titles: list[str], query: str) -> str:
    """추천 제목 리스트에서 부분 매칭(case-insensitive). 0개 또는 2개+ 매칭 시 예외."""
    q = query.strip().lower()
    matches = [t for t in rec_titles if q in t.lower()]
    if not matches:
        raise ValueError(
            f"'{query}' 에 매칭되는 추천 없음. 가능한 제목: {rec_titles}"
        )
    if len(matches) > 1:
        raise ValueError(
            f"'{query}' 모호함 ({len(matches)}개 매칭): {matches}. "
            f"더 긴 부분 문자열로 다시 시도."
        )
    return matches[0]


def mark_recommendation_acted(
    rec_id: int, title_query: str, *, undo: bool = False
) -> None:
    """추천을 '실제 시작함' 으로 표시 (또는 --undo로 취소).

    title_query는 부분 문자열 매칭 (case-insensitive). 정확히 1개와 매칭되어야 함.
    """
    init_db()
    session = get_session()
    try:
        rec = session.query(Recommendation).filter(
            Recommendation.id == rec_id
        ).one_or_none()
        if rec is None:
            raise RuntimeError(
                f"rec_id={rec_id} 추천 없음. "
                f"[cyan]vibe recommend --history[/cyan] 로 ID 확인."
            )

        rec_titles = [
            r.get("title", "")
            for r in (rec.payload or {}).get("recommendations", [])
        ]
        matched = _resolve_title(rec_titles, title_query)

        # JSON 컬럼 in-place 변경은 SQLAlchemy가 감지 못 함 → 새 리스트 할당
        acted_on = list(rec.acted_on or [])
        if undo:
            if matched not in acted_on:
                console.print(
                    f"[yellow]'{matched}' 는 이미 미표시 상태 (rec_id={rec_id})[/yellow]"
                )
                return
            acted_on.remove(matched)
            rec.acted_on = acted_on
            session.commit()
            console.print(
                f"[green]✓ 표시 취소: '{matched}' (rec_id={rec_id})[/green]"
            )
        else:
            if matched in acted_on:
                console.print(
                    f"[yellow]'{matched}' 는 이미 acted 표시됨 (rec_id={rec_id})[/yellow]"
                )
                return
            acted_on.append(matched)
            rec.acted_on = acted_on
            session.commit()
            console.print(
                f"[green]✓ '{matched}' 시작함 표시 완료 (rec_id={rec_id})[/green]"
            )
    finally:
        session.close()
