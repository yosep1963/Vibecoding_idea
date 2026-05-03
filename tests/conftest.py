"""공용 fixture: 가짜 Repo/Analysis 객체 생성기."""
from datetime import datetime, timedelta
from typing import Any

import pytest

from src.models import Analysis, Repo

_UNSET = object()  # 명시적 None과 default 미지정을 구분


def make_repo(
    *,
    id: int = 1,
    name: str = "test-repo",
    description: str | None = "테스트 레포",
    language: str | None = "Python",
    topics: list[str] | None = None,
    readme: str | None = "# Test\n간단한 README",
    package_files: dict[str, str] | None = None,
    is_archived: int = 0,
    pushed_at: Any = _UNSET,
) -> Repo:
    """SQLAlchemy session 없이도 인스턴스만 만들어 함수 입력으로 사용.

    pushed_at: 미지정 시 utcnow(). 명시적 None을 구분하기 위해 sentinel 사용.
    """
    return Repo(
        id=id,
        name=name,
        full_name=f"user/{name}",
        description=description,
        language=language,
        topics=topics if topics is not None else [],
        stars=0,
        forks=0,
        is_fork=0,
        is_archived=is_archived,
        created_at=datetime(2026, 1, 1),
        pushed_at=datetime.utcnow() if pushed_at is _UNSET else pushed_at,
        readme=readme,
        package_files=package_files if package_files is not None else {},
    )


def make_analysis(
    *,
    repo_id: int = 1,
    domain: str = "임상AI",
    form: str = "CLI",
    status: str = "active",
    cluster_id: int | None = 0,
) -> Analysis:
    return Analysis(
        repo_id=repo_id,
        domain=domain,
        form=form,
        status=status,
        cluster_id=cluster_id,
    )


@pytest.fixture
def repo_factory():
    return make_repo


@pytest.fixture
def analysis_factory():
    return make_analysis
