# CLAUDE.md

> hepatoscores-py — Vibe Idea Generator가 생성한 초기 컨텍스트.

## 프로젝트

**hepatoscores-py** — 간장학 핵심 점수 계산기 10종을 하나의 pip 설치 가능한 Python 패키지로 통합

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

MELD·FIB4·child-pugh·ALBI-BCLC·CLIF-C-ACLF/OF/AD·Lille-model·Liver-Fibrosis-Calculator 각 레포의 계산 로직 함수 직접 이식 (대부분 순수 수식 함수라 이식 비용 거의 없음)

## 새로 배울 것

pytest 기반 단위 테스트 작성 (논문 기준값 검증), uv publish로 PyPI 배포 파이프라인

## 왜 의미있는가

30년 임상 지식이 녹아 있는 계산기 10개가 지금 개별 레포로 분산되어 인용·재사용 불가 상태. 단일 패키지로 묶으면 논문 Materials에 'pip install hepatoscores-py'로 방법론 공개 가능 → CLINICCAI 2026 이후 연구 재현성 확보 및 타 의료 AI 개발자 기여 기반

## 첫 PR 단계

1. uv init hepatoscores-py + MELD·FIB4·Child-Pugh 세 함수 이식 및 논문 기준값 기반 pytest 3개 작성
2. CLIF-C-ACLF·OF·AD·Lille·ALBI-BCLC·Liver-Fibrosis 함수 추가 + 모든 테스트 green 확인
3. pyproject.toml 메타데이터(classifiers: medicine, hepatology) 완성 후 TestPyPI 배포 및 README에 코드 예시 추가

## 기술 스택 (제안)

> Vibe Idea Gen이 추천한 형태(라이브러리)에 맞춰 사용자가 직접 결정.
> 기존 레포의 패턴 참고할 것.

## 코딩 규약

- 경로: `pathlib.Path` 필수 (Windows 호환)
- 한국어 주석 OK
- 작은 샘플로 먼저 테스트
