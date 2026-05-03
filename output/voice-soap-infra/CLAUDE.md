# CLAUDE.md

> voice-soap-infra — Vibe Idea Generator가 생성한 초기 컨텍스트.

## 프로젝트

**voice-soap-infra** — Voice-SOAP CLI를 Docker + Caddy 리버스프록시로 셀프호스팅하는 인프라 구성 레포

## 사용자 컨텍스트 (모든 LLM 호출에 주입)

- 직업: 대구가톨릭대학교 의과대학 소화기내과 교수 (간장학)
- 임상 30년차, 2028년 8월 정년
- 개발 스타일: Vibe coding, 임상 AI + 풀스택 웹앱이 주력
- 한국어 응답 선호

## 분류

- 도메인: 인프라도구
- 형태: CLI
- 예상 소요: 1-2주

## 재사용 자산

Voice-SOAP의 pyproject.toml 엔트리포인트와 CLAUDE.md 구조를 그대로 참조; second 레포(CLAUDE.md만 존재, 현재 인프라도구+기타 분류)의 미완성 설정 파일을 이 레포로 흡수

## 새로 배울 것

Caddyfile 자동 TLS 설정, Docker multi-stage build로 Python CLI를 HTTP 엔드포인트로 래핑(FastAPI 최소 래퍼)

## 왜 의미있는가

인프라도구 도메인이 레포 1개(second)뿐이고 CLI 형태는 완전 비어 있음. Voice-SOAP는 현재 로컬 CLI 전용이라 병동 EMR 연동이 불가능. FastAPI 래퍼 + Caddy HTTPS를 붙이면 스마트폰에서 음성 녹음 → 즉시 SOAP 생성 워크플로가 실제 병동에서 돌아가는 수준이 됨.

## 첫 PR 단계

1. Voice-SOAP를 FastAPI /transcribe 엔드포인트로 감싸는 최소 래퍼 작성(app/main.py 50줄 이내)
2. Dockerfile multi-stage(builder: poetry install, runner: 최소 이미지) + docker-compose.yml 작성
3. Caddyfile에 도메인 + reverse_proxy 설정 추가 후 로컬 HTTPS 동작 확인, README에 1-command 배포 가이드 작성

## 기술 스택 (제안)

> Vibe Idea Gen이 추천한 형태(CLI)에 맞춰 사용자가 직접 결정.
> 기존 레포의 패턴 참고할 것.

## 코딩 규약

- 경로: `pathlib.Path` 필수 (Windows 호환)
- 한국어 주석 OK
- 작은 샘플로 먼저 테스트
