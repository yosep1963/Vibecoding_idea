"""LLM 래퍼: Ollama (로컬, 임베딩+분류) + Anthropic Claude (Phase 3 추천).

설계 원칙(CLAUDE.md):
- 로컬 우선. Claude API는 최종 추천에만 호출.
- 모든 사용자 컨텍스트 주입 프롬프트에는 "간장학 교수" 명시.
"""
from __future__ import annotations

import json
from typing import Any

import httpx
import ollama

from .config import config

# Phase 2 기본 모델
EMBED_MODEL = "bge-m3"          # 한국어+영어 혼합에 강함, 1024 dim
TAG_MODEL = "qwen2.5:14b"       # 로컬 카테고리 태깅용

# 사용자 컨텍스트 (모든 LLM 호출에 주입)
USER_CONTEXT = """\
사용자: 대구가톨릭대학교 의과대학 소화기내과 교수, 간장학 전공, 임상 30년차.
개발 스타일: Vibe coding, 임상 AI + 풀스택 웹앱이 주력.
진행 중: AsterixisNet (간성혼수 손떨림 검출), Voice-SOAP (음성→간장학 SOAP), TodoList 풀스택 앱.
"""


class OllamaClient:
    """Ollama 로컬 LLM 래퍼."""

    def __init__(self, host: str | None = None):
        self.host = host or config.OLLAMA_HOST
        self._client = ollama.Client(host=self.host)

    def embed(self, text: str, model: str = EMBED_MODEL) -> list[float]:
        """단일 텍스트 임베딩."""
        resp = self._client.embeddings(model=model, prompt=text)
        return list(resp["embedding"])

    def chat_json(
        self,
        prompt: str,
        *,
        model: str = TAG_MODEL,
        system: str | None = None,
        temperature: float = 0.1,
    ) -> dict[str, Any]:
        """JSON 응답 강제. 파싱 실패 시 빈 dict."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        resp = self._client.chat(
            model=model,
            messages=messages,
            format="json",
            options={"temperature": temperature},
        )
        content = resp["message"]["content"]
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {}

    def health(self) -> bool:
        """Ollama 서버 연결 확인."""
        try:
            httpx.get(f"{self.host}/api/tags", timeout=3.0).raise_for_status()
            return True
        except httpx.HTTPError:
            return False

    def has_model(self, name: str) -> bool:
        """모델 설치 여부 확인. tag 생략 시 prefix 매칭."""
        try:
            tags = self._client.list()
            models = tags.get("models", [])
            for m in models:
                model_name = m.get("model") or m.get("name", "")
                if model_name == name or model_name.startswith(f"{name}:"):
                    return True
            return False
        except Exception:
            return False


def get_anthropic_client():
    """Phase 3에서만 lazy import. Phase 2 사용 시 anthropic 미설정도 OK."""
    import anthropic
    if not config.ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY 미설정. .env 확인.")
    return anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
