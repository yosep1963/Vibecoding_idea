# CLAUDE.md

> HE-Staging-Notebook — Vibe Idea Generator가 생성한 초기 컨텍스트.

## 프로젝트

**HE-Staging-Notebook** — Asterixis 시리즈의 원시 가속도계 데이터를 West Haven 등급과 매핑하는 탐색적 분석 노트북

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

asterixis-0414의 requirements.txt + 전처리 파이프라인, HE_irb의 IRB 데이터 구조 및 West Haven 스코어링 로직, HE_CMP의 임상 변수 정의

## 새로 배울 것

Jupyter nbformat 기반 재현가능 연구 구조화 (papermill 또는 quarto), statsmodels ROC/AUC 곡선으로 떨림 threshold vs. West Haven 등급 간 cut-off 도출

## 왜 의미있는가

Asterixis 레포가 4개(cluster_0, cluster_2)인데 모두 CLI/PWA 형태라 원시 데이터→임상 해석 연결 고리가 없음. 논문 제출 시 재현가능한 분석 근거가 노트북 형태로 존재해야 하며, 간성혼수 staging의 정량 근거를 30년 임상 경험으로 직접 레이블링한 데이터셋이 가장 큰 자산

## 첫 PR 단계

1. asterixis-0414 raw CSV를 notebooks/data/ 에 버전 고정 후 DVC 또는 Git LFS로 추적 설정
2. West Haven grade별 가속도계 feature(RMS, tremor frequency band 4-12Hz) 분포를 seaborn violin plot으로 시각화하는 EDA 셀 작성
3. sklearn LogisticRegression + LOOCV로 grade 0 vs ≥1 분류 AUC 계산 및 95% CI 출력 셀 추가

## 기술 스택 (제안)

> Vibe Idea Gen이 추천한 형태(노트북)에 맞춰 사용자가 직접 결정.
> 기존 레포의 패턴 참고할 것.

## 코딩 규약

- 경로: `pathlib.Path` 필수 (Windows 호환)
- 한국어 주석 OK
- 작은 샘플로 먼저 테스트
