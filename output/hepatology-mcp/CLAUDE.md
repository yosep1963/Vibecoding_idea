# CLAUDE.md

> hepatology-mcp — Vibe Idea Generator가 생성한 초기 컨텍스트.

## 프로젝트

**hepatology-mcp** — MELD·FIB4 등 간장학 계산기와 임상 컨텍스트를 Claude에 직접 노출하는 MCP 서버

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

hepatoscores-py(위 추천 1)의 계산 함수 전체를 MCP tool로 래핑, Voice-SOAP의 임상 SOAP 컨텍스트 설계(프롬프트 구조), vibe-idea-gen의 typer+uv 프로젝트 골격

## 새로 배울 것

FastMCP 또는 Python MCP SDK의 @tool·@resource 데코레이터 패턴, Claude Desktop mcp_servers 설정 방법

## 왜 의미있는가

현재 Claude Code로 Voice-SOAP 작성 시 MELD 점수를 수동으로 계산기 레포에서 확인 후 붙여넣는 이중 작업 발생. MCP 서버를 띄우면 Claude가 대화 중 'calc_meld(Na=138, Cr=1.8, bili=4.2, INR=1.6)' 직접 호출 → 간장학 AI 프로젝트 전체의 인프라 허브로 작동. 37개 레포 중 유일한 인프라 레이어가 될 것

## 첫 PR 단계

1. FastMCP 설치 + calc_meld()·calc_fib4() 두 tool 노출 후 Claude Desktop mcp_servers에 등록하여 자연어 호출 동작 확인
2. hepatoscores-py 전체 함수를 tool로 확장 + 각 tool description을 한국어 의학 용어(간장학 전문의 기준)로 작성
3. Voice-SOAP 시스템 프롬프트에 MCP 도구 호출 지시 추가 → SOAP 작성 중 실시간 점수 계산 통합 end-to-end 테스트

## 기술 스택 (제안)

> Vibe Idea Gen이 추천한 형태(CLI)에 맞춰 사용자가 직접 결정.
> 기존 레포의 패턴 참고할 것.

## 코딩 규약

- 경로: `pathlib.Path` 필수 (Windows 호환)
- 한국어 주석 OK
- 작은 샘플로 먼저 테스트
