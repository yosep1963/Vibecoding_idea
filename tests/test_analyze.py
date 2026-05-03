"""analyze.py 의 순수 함수들 단위 테스트."""
from datetime import datetime, timedelta

import numpy as np

from src.analyze import (
    EMBED_TEXT_MAX,
    README_HEAD_LEN,
    array_to_blob,
    blob_to_array,
    build_embed_text,
    determine_status,
)
from tests.conftest import make_repo


# === build_embed_text ===


def test_build_embed_text_includes_all_fields():
    repo = make_repo(
        description="간성혼수 손떨림 검출",
        topics=["medical-ai", "asterixis"],
        language="Python",
        readme="# Asterixis\n손떨림 영상 분류 모델",
        package_files={"pyproject.toml": "...", "requirements.txt": "..."},
    )
    text = build_embed_text(repo)
    assert "간성혼수 손떨림 검출" in text
    assert "medical-ai" in text
    assert "asterixis" in text
    assert "Python" in text
    assert "Asterixis" in text
    assert "pyproject.toml" in text


def test_build_embed_text_truncates_to_max():
    long_readme = "X" * 50000
    repo = make_repo(readme=long_readme)
    text = build_embed_text(repo)
    assert len(text) <= EMBED_TEXT_MAX


def test_build_embed_text_truncates_readme_head():
    long_readme = "Y" * 50000
    repo = make_repo(description=None, topics=[], language=None,
                     package_files={}, readme=long_readme)
    text = build_embed_text(repo)
    # README 헤드 컷 + 전체 컷이 둘 다 적용되어야 함
    assert "Y" * (README_HEAD_LEN + 1) not in text


def test_build_embed_text_handles_missing_fields():
    repo = make_repo(
        description=None, topics=[], language=None,
        readme=None, package_files={},
    )
    text = build_embed_text(repo)
    # 모든 필드가 None이어도 예외 없이 빈 문자열 또는 일부 반환
    assert isinstance(text, str)


# === determine_status ===


def test_determine_status_archived():
    repo = make_repo(is_archived=1)
    assert determine_status(repo) == "archived"


def test_determine_status_active_recent_push():
    repo = make_repo(pushed_at=datetime.utcnow() - timedelta(days=10))
    assert determine_status(repo) == "active"


def test_determine_status_abandoned_old_push():
    repo = make_repo(pushed_at=datetime.utcnow() - timedelta(days=400))
    assert determine_status(repo) == "abandoned"


def test_determine_status_no_push():
    repo = make_repo(pushed_at=None)
    assert determine_status(repo) == "abandoned"


def test_determine_status_middle_age():
    # 90일 ~ 365일 사이는 active 로 분류
    repo = make_repo(pushed_at=datetime.utcnow() - timedelta(days=180))
    assert determine_status(repo) == "active"


# === array_to_blob / blob_to_array 라운드트립 ===


def test_blob_roundtrip_preserves_values():
    arr = np.array([1.0, 2.5, -3.14, 0.0, 1e-6], dtype=np.float32)
    blob = array_to_blob(arr)
    restored = blob_to_array(blob)
    assert np.allclose(restored, arr)


def test_blob_roundtrip_preserves_length():
    arr = np.random.randn(1024).astype(np.float32)  # bge-m3 임베딩 길이
    blob = array_to_blob(arr)
    restored = blob_to_array(blob)
    assert restored.shape == arr.shape


def test_array_to_blob_casts_float64_to_float32():
    arr = np.array([1.0, 2.0], dtype=np.float64)
    blob = array_to_blob(arr)
    # float32(4byte) × 2개 = 8 bytes
    assert len(blob) == 8
