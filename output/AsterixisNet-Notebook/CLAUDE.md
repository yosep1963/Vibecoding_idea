# CLAUDE.md

> AsterixisNet-Notebook — Vibe Idea Generator가 생성한 초기 컨텍스트.

## 프로젝트

**AsterixisNet-Notebook** — CLINICCAI 2026 제출용 간성혼수 손떨림 검출 모델의 재현 가능한 end-to-end 실험 노트북

## 사용자 컨텍스트 (모든 LLM 호출에 주입)

- 직업: 대구가톨릭대학교 의과대학 소화기내과 교수 (간장학)
- 임상 30년차, 2028년 8월 정년
- 개발 스타일: Vibe coding, 임상 AI + 풀스택 웹앱이 주력
- 한국어 응답 선호

## 분류

- 도메인: 임상AI
- 형태: 노트북
- 예상 소요: 주말

## 재사용 자산

asterixis-0414의 모델 학습 코드 전체, Asterixis_smartphone의 스마트폰 센서 전처리 파이프라인, HE_irb의 IRB 데이터 로딩 로직

## 새로 배울 것

papermill로 hyperparameter를 외부 파라미터 셀로 분리 (배치 실험 자동화), nbconvert로 HTML·PDF 보고서 생성

## 왜 의미있는가

CLINICCAI 2026 심사에서 재현 가능성(reproducibility)은 채점 항목. 현재 코드는 .py 스크립트로 분산되어 있어 심사자가 실행 흐름 파악 불가. 전처리→학습→평가→시각화 전 과정을 단일 노트북으로 공개하면 논문 credibility 직접 보강 + 정년 후 연구 자산 아카이빙

## 첫 PR 단계

1. asterixis-0414 전처리 코드를 01_preprocessing.ipynb 셀로 분해 + 샘플 데이터 5건 smoke-test 통과 확인
2. 모델 학습 셀 추가 후 hyperparameter(window_size, lr, epochs)를 papermill 파라미터 셀로 외부화 및 3-epoch 실행 검증
3. Confusion matrix·ROC curve·loss curve 시각화 셀 완성 + nbconvert HTML 보고서 생성 Makefile 1줄 추가

## 기술 스택 (제안)

> Vibe Idea Gen이 추천한 형태(노트북)에 맞춰 사용자가 직접 결정.
> 기존 레포의 패턴 참고할 것.

## 코딩 규약

- 경로: `pathlib.Path` 필수 (Windows 호환)
- 한국어 주석 OK
- 작은 샘플로 먼저 테스트
