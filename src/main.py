"""CLI 엔트리포인트.

사용법:
    uv run vibe collect              # GitHub 레포 수집
    uv run vibe stats                # 저장된 데이터 요약
    uv run vibe show <레포명>        # 특정 레포 상세 보기
    uv run vibe analyze              # Phase 2: 임베딩 + 카테고리 + 클러스터
    uv run vibe clusters             # 클러스터별 레포 출력
    uv run vibe recommend            # Phase 3: Claude API 추천 3개
    uv run vibe recommend --history  # 과거 추천 이력
"""
from __future__ import annotations

import asyncio

import typer
from rich.console import Console
from rich.table import Table

from .analyze import run_analyze, show_clusters
from .collect import collect_all
from .models import Repo, get_session, init_db
from .recommend import run_recommend, show_recommend_history

app = typer.Typer(
    help="Vibe Idea Generator - 본인 패턴 기반 다음 프로젝트 추천",
    no_args_is_help=True,
)
console = Console()


@app.command()
def collect(
    include_forks: bool = typer.Option(
        False, "--include-forks", help="fork한 레포도 포함"
    ),
    include_archived: bool = typer.Option(
        False, "--include-archived", help="archive된 레포도 포함"
    ),
):
    """GitHub에서 본인 레포 수집 → SQLite 저장."""
    try:
        count = asyncio.run(
            collect_all(
                skip_forks=not include_forks,
                skip_archived=not include_archived,
            )
        )
        console.print(f"\n[bold]다음 단계:[/bold] [cyan]uv run vibe stats[/cyan]")
    except ValueError as e:
        console.print(f"[bold red]설정 오류:[/bold red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]오류:[/bold red] {e}")
        raise typer.Exit(1)


@app.command()
def stats():
    """저장된 레포 데이터 요약 통계."""
    init_db()
    session = get_session()
    try:
        repos = session.query(Repo).all()

        if not repos:
            console.print(
                "[yellow]저장된 레포가 없습니다. 먼저 [cyan]vibe collect[/cyan]를 실행하세요.[/yellow]"
            )
            return

        # 요약
        console.print(f"\n[bold cyan]전체 레포: {len(repos)}개[/bold cyan]\n")

        # 언어별 분포
        lang_count: dict[str, int] = {}
        for r in repos:
            lang = r.language or "(없음)"
            lang_count[lang] = lang_count.get(lang, 0) + 1

        table = Table(title="언어별 분포", show_header=True, header_style="bold magenta")
        table.add_column("언어", style="cyan")
        table.add_column("개수", justify="right")

        for lang, count in sorted(
            lang_count.items(), key=lambda x: -x[1]
        ):
            table.add_row(lang, str(count))
        console.print(table)

        # 최근 push된 상위 10개
        recent = sorted(
            [r for r in repos if r.pushed_at],
            key=lambda r: r.pushed_at,
            reverse=True,
        )[:10]

        table2 = Table(
            title="\n최근 작업한 레포 Top 10",
            show_header=True,
            header_style="bold magenta",
        )
        table2.add_column("이름", style="cyan")
        table2.add_column("언어")
        table2.add_column("⭐", justify="right")
        table2.add_column("마지막 push")
        table2.add_column("README", justify="center")

        for r in recent:
            table2.add_row(
                r.name,
                r.language or "-",
                str(r.stars),
                r.pushed_at.strftime("%Y-%m-%d") if r.pushed_at else "-",
                "✓" if r.readme else "✗",
            )
        console.print(table2)

        # 메타: README/deps 보유율
        with_readme = sum(1 for r in repos if r.readme)
        with_deps = sum(1 for r in repos if r.package_files)
        with_claude_md = sum(
            1 for r in repos
            if r.package_files and "CLAUDE.md" in r.package_files
        )

        console.print(
            f"\n[dim]README 보유: {with_readme}/{len(repos)} | "
            f"의존성 파일: {with_deps}/{len(repos)} | "
            f"CLAUDE.md: {with_claude_md}/{len(repos)}[/dim]"
        )

    finally:
        session.close()


@app.command()
def show(name: str = typer.Argument(..., help="레포 이름")):
    """특정 레포의 상세 정보 출력."""
    init_db()
    session = get_session()
    try:
        repo = session.query(Repo).filter_by(name=name).first()
        if not repo:
            console.print(f"[red]레포 '{name}'을 찾을 수 없습니다.[/red]")
            raise typer.Exit(1)

        console.print(f"\n[bold cyan]{repo.full_name}[/bold cyan]")
        console.print(f"[dim]{repo.description or '(설명 없음)'}[/dim]\n")

        console.print(f"언어: {repo.language or '-'}")
        console.print(f"토픽: {', '.join(repo.topics) if repo.topics else '-'}")
        console.print(f"스타: {repo.stars} | 포크: {repo.forks}")
        console.print(
            f"생성: {repo.created_at.strftime('%Y-%m-%d') if repo.created_at else '-'} | "
            f"최근 push: {repo.pushed_at.strftime('%Y-%m-%d') if repo.pushed_at else '-'}"
        )
        console.print(
            f"의존성 파일: {list(repo.package_files.keys()) if repo.package_files else '없음'}"
        )

        if repo.readme:
            console.print("\n[bold]README (앞 500자):[/bold]")
            console.print(repo.readme[:500])

    finally:
        session.close()


@app.command()
def analyze(
    rerun: bool = typer.Option(
        False, "--rerun", help="이미 임베딩된 레포도 재처리"
    ),
    k: int = typer.Option(6, "--k", help="KMeans 클러스터 개수"),
):
    """Phase 2: Ollama 임베딩 + 카테고리 태깅 + 클러스터링."""
    try:
        run_analyze(rerun=rerun, k=k)
        console.print(
            f"\n[bold]다음 단계:[/bold] [cyan]uv run vibe clusters[/cyan]"
        )
    except (RuntimeError, ValueError) as e:
        console.print(f"[bold red]오류:[/bold red] {e}")
        raise typer.Exit(1)


@app.command()
def clusters():
    """클러스터별 레포 목록 출력."""
    show_clusters()


@app.command()
def recommend(
    history: bool = typer.Option(
        False, "--history", help="과거 추천 이력 출력 (생성 안 함)"
    ),
):
    """Phase 3: 빈틈 분석 + Claude API로 다음 프로젝트 3개 추천."""
    if history:
        show_recommend_history()
        return
    try:
        run_recommend()
    except (RuntimeError, ValueError) as e:
        console.print(f"[bold red]오류:[/bold red] {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
