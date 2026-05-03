# CLAUDE.md

> hepatox-lib — Vibe Idea Generator가 생성한 초기 컨텍스트.

## 프로젝트

**hepatox-lib** — hepatotoxicity-checker와 CYP450의 핵심 판정 로직을 npm 패키지로 추출해 재사용 가능한 간독성 판정 라이브러리

## 사용자 컨텍스트 (모든 LLM 호출에 주입)

- 직업: 대구가톨릭대학교 의과대학 소화기내과 교수 (간장학)
- 임상 30년차, 2028년 8월 정년
- 개발 스타일: Vibe coding, 임상 AI + 풀스택 웹앱이 주력
- 한국어 응답 선호

## 분류

- 도메인: 임상AI
- 형태: 라이브러리
- 예상 소요: 1-2주

## 재사용 자산

hepatotoxicity-checker(TypeScript)의 DILI 판정 알고리즘 및 약물 데이터, CYP450(TypeScript)의 상호작용 매핑 테이블, Liver-Fibrosis-Calculator의 점수 계산 유틸 패턴

## 새로 배울 것

tsup 번들러로 ESM/CJS 듀얼 패키지 빌드 및 npm publish 워크플로, Vitest 기반 임상 엣지케이스 단위 테스트(예: Hy's Law 경계값)

## 왜 의미있는가

hepatotoxicity-checker와 CYP450이 각각 독립 웹앱으로 존재하지만 Livercare_LC 같은 통합 앱에 내장하거나 Voice-SOAP의 처방 검토 단계에 붙이려면 라이브러리 추출이 필수. '임상AI+라이브러리' 조합이 현재 0개인 가장 큰 공백이며, 간독성 판정 로직은 교수 본인의 임상 지식이 직접 코드화된 희소 자산

## 첫 PR 단계

1. hepatotoxicity-checker에서 순수 함수(약물명→DILI 위험등급 반환)만 src/core/ 로 분리하고 UI 의존성 제거
2. CYP450 상호작용 테이블을 JSON Schema로 정의하고 타입 안전하게 쿼리하는 checkInteraction(drugA, drugB) 함수 작성
3. GitHub Actions로 main 푸시 시 npm publish --dry-run 실행하는 CI 파이프라인 구성

## 기술 스택 (제안)

> Vibe Idea Gen이 추천한 형태(라이브러리)에 맞춰 사용자가 직접 결정.
> 기존 레포의 패턴 참고할 것.

## 코딩 규약

- 경로: `pathlib.Path` 필수 (Windows 호환)
- 한국어 주석 OK
- 작은 샘플로 먼저 테스트
