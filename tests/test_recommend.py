"""recommend.py 의 순수 함수들 단위 테스트."""
import json

import pytest

from src.recommend import build_repo_summary, extract_json, safe_dirname
from tests.conftest import make_analysis, make_repo


# === safe_dirname ===


def test_safe_dirname_replaces_forbidden_chars():
    name = 'my:project/with*bad?chars'
    result = safe_dirname(name)
    for ch in ':/*?<>|"\\':
        assert ch not in result


def test_safe_dirname_collapses_whitespace():
    result = safe_dirname("hello   world")
    assert " " not in result


def test_safe_dirname_strips_leading_trailing_underscores():
    result = safe_dirname("///hello///")
    assert not result.startswith("_")
    assert not result.endswith("_")


def test_safe_dirname_caps_length():
    long = "a" * 200
    result = safe_dirname(long)
    assert len(result) <= 60


def test_safe_dirname_keeps_safe_chars():
    result = safe_dirname("hepatox-notebook")
    assert result == "hepatox-notebook"


# === extract_json ===


def test_extract_json_from_raw_object():
    text = '{"recommendations": [{"title": "x"}]}'
    result = extract_json(text)
    assert result == {"recommendations": [{"title": "x"}]}


def test_extract_json_from_markdown_fence():
    text = '여기 결과:\n```json\n{"recommendations": [{"title": "x"}]}\n```\n끝.'
    result = extract_json(text)
    assert result["recommendations"][0]["title"] == "x"


def test_extract_json_from_text_with_prefix():
    text = '아래는 추천입니다.\n{"recommendations": []}\n끝.'
    result = extract_json(text)
    assert result == {"recommendations": []}


def test_extract_json_invalid_raises():
    with pytest.raises(json.JSONDecodeError):
        extract_json("아무런 JSON도 없는 평문 텍스트")


# === build_repo_summary ===


def test_build_repo_summary_counts_total():
    pairs = [
        (make_repo(id=1, name=f"r{i}"),
         make_analysis(repo_id=1, domain="임상AI", form="CLI"))
        for i in range(5)
    ]
    summary = build_repo_summary(pairs)
    assert summary["total_repos"] == 5


def test_build_repo_summary_matrix_aggregates_counts():
    pairs = [
        (make_repo(id=1, name="a"),
         make_analysis(repo_id=1, domain="임상AI", form="CLI")),
        (make_repo(id=2, name="b"),
         make_analysis(repo_id=2, domain="임상AI", form="CLI")),
        (make_repo(id=3, name="c"),
         make_analysis(repo_id=3, domain="풀스택웹앱", form="웹앱")),
    ]
    summary = build_repo_summary(pairs)
    assert summary["domain_form_matrix"]["임상AI|CLI"] == 2
    assert summary["domain_form_matrix"]["풀스택웹앱|웹앱"] == 1


def test_build_repo_summary_identifies_empty_combinations():
    # 단 1개 조합만 채움 → 나머지 의미있는 조합은 모두 empty
    pairs = [
        (make_repo(id=1, name="only"),
         make_analysis(repo_id=1, domain="임상AI", form="CLI")),
    ]
    summary = build_repo_summary(pairs)
    # 임상AI+노트북 등은 비어 있어야 함
    assert any("임상AI+노트북" == c for c in summary["empty_combinations"])
    assert any("풀스택웹앱+웹앱" == c for c in summary["empty_combinations"])


def test_build_repo_summary_excludes_other_from_empty():
    """domain="기타" 또는 form="기타"는 의미있는 조합에서 제외."""
    pairs = []
    summary = build_repo_summary(pairs)
    for combo in summary["empty_combinations"]:
        assert "기타" not in combo


def test_build_repo_summary_groups_clusters():
    pairs = [
        (make_repo(id=1, name="a"),
         make_analysis(repo_id=1, cluster_id=0)),
        (make_repo(id=2, name="b"),
         make_analysis(repo_id=2, cluster_id=0)),
        (make_repo(id=3, name="c"),
         make_analysis(repo_id=3, cluster_id=1)),
    ]
    summary = build_repo_summary(pairs)
    assert sorted(summary["clusters"]["cluster_0"]) == ["a", "b"]
    assert summary["clusters"]["cluster_1"] == ["c"]


def test_build_repo_summary_inventory_truncates_description():
    long_desc = "X" * 500
    pairs = [
        (make_repo(id=1, name="a", description=long_desc),
         make_analysis(repo_id=1)),
    ]
    summary = build_repo_summary(pairs)
    assert len(summary["inventory"][0]["desc"]) <= 120


def test_build_repo_summary_sparse_combinations_only_count_one():
    pairs = [
        (make_repo(id=1, name="a"),
         make_analysis(repo_id=1, domain="임상AI", form="라이브러리")),
        # 다른 조합은 2개 이상이면 sparse 아님
        (make_repo(id=2, name="b"),
         make_analysis(repo_id=2, domain="풀스택웹앱", form="웹앱")),
        (make_repo(id=3, name="c"),
         make_analysis(repo_id=3, domain="풀스택웹앱", form="웹앱")),
    ]
    summary = build_repo_summary(pairs)
    sparse_str = " ".join(summary["sparse_combinations"])
    assert "임상AI+라이브러리" in sparse_str
    assert "풀스택웹앱+웹앱" not in sparse_str
