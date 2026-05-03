# CLAUDE.md

> hepatox-notebook — Vibe Idea Generator가 생성한 초기 컨텍스트.

## 프로젝트

**hepatox-notebook** — 약인성 간손상(DILI) 임상 데이터셋을 EDA→모델 비교→SHAP 해석까지 재현 가능한 분석 노트북

## 사용자 컨텍스트 (모든 LLM 호출에 주입)

- 직업: 대구가톨릭대학교 의과대학 소화기내과 교수 (간장학)
- 임상 30년차, 2028년 8월 정년
- 개발 스타일: Vibe coding, 임상 AI + 풀스택 웹앱이 주력
- 한국어 응답 선호

## 분류

- 도메인: 임상AI
- 형태: 노트북
- 예상 소요: 1-2주

## 재사용 자산

hepatotoxicity-checker의 약물-간독성 판정 로직(TypeScript)을 Python으로 역포팅하여 feature 정의에 활용; ALBI-BCLC의 requirements.txt 의존성 스택(pandas/scikit-learn) 그대로 복용

## 새로 배울 것

SHAP TreeExplainer waterfall plot, nbformat 기반 재현 가능 노트북 구조(papermill 파라미터화)

## 왜 의미있는가

임상AI 도메인에 노트북 형태가 전무(empty 조합). hepatotoxicity-checker는 웹앱으로만 존재해 모델 의사결정 근거가 블랙박스임. 30년 임상 경험에서 나온 DILI 판단 기준을 SHAP으로 가시화하면 IRB 제출 근거 자료로도 직결됨.

## 첫 PR 단계

1. hepatotoxicity-checker의 판정 규칙을 Python 함수로 변환하고 단위 테스트 작성
2. 공개 DILI 데이터셋(DILIrank 또는 LiverTox) 로드 → 기술통계 EDA 섹션 완성
3. RandomForest vs XGBoost AUROC 비교 후 SHAP waterfall 1개 케이스 시각화

## 기술 스택 (제안)

> Vibe Idea Gen이 추천한 형태(노트북)에 맞춰 사용자가 직접 결정.
> 기존 레포의 패턴 참고할 것.

## 코딩 규약

- 경로: `pathlib.Path` 필수 (Windows 호환)
- 한국어 주석 OK
- 작은 샘플로 먼저 테스트
