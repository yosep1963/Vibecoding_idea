# CLAUDE.md

> LiverScore-Dashboard — Vibe Idea Generator가 생성한 초기 컨텍스트.

## 프로젝트

**LiverScore-Dashboard** — MELD·ALBI·CLIF-C·Child-Pugh 등 기존 계산기 레포를 한 화면에서 환자 한 명에게 동시 계산하는 임상 의사결정 대시보드

## 사용자 컨텍스트 (모든 LLM 호출에 주입)

- 직업: 대구가톨릭대학교 의과대학 소화기내과 교수 (간장학)
- 임상 30년차, 2028년 8월 정년
- 개발 스타일: Vibe coding, 임상 AI + 풀스택 웹앱이 주력
- 한국어 응답 선호

## 분류

- 도메인: 임상AI
- 형태: PWA
- 예상 소요: 1개월+

## 재사용 자산

MELD·child-pugh·CLIF-C-ACLF·CLIF-C-OF·CLIF-C-AD·ALBI-BCLC의 점수 계산 로직 전체, Health_Planner(TypeScript PWA)의 서비스워커·오프라인 캐시 설정, Livercare_LC의 TypeScript 컴포넌트 구조

## 새로 배울 것

Zustand 또는 Jotai로 환자 컨텍스트(단일 입력값 세트)를 여러 점수 계산기에 동시 전파하는 상태 설계, PWA Background Sync로 오프라인 입력값 저장 후 온라인 시 자동 동기화

## 왜 의미있는가

cluster_2 레포 9개(SOFA, MELD, FIB4, child-pugh, CLIF-C류 등)가 각각 별도 URL로 존재해 실제 회진에서 탭을 여러 개 열어야 하는 비효율이 있음. 간경변 환자 한 명의 LAB 값을 한 번 입력하면 모든 예후 점수가 동시 계산되는 PWA는 30년 임상 경험자가 '실제로 쓸' 도구이며, '임상AI+PWA'가 현재 1개(sparse)인 공백을 채움

## 첫 PR 단계

1. 기존 계산기 레포에서 순수 계산 함수만 packages/scores/ 모노레포 패키지로 추출 (turborepo 초기화)
2. 공통 PatientInput 타입(Cr, Na, Bili, INR, albumin, PT 등) 정의 후 각 점수 함수의 입력 인터페이스로 매핑
3. 단일 폼 입력→MELD-Na·Child-Pugh·ALBI·CLIF-C-OF 4개 점수 동시 출력하는 MVP 화면 구현 및 PWA manifest+서비스워커 추가

## 기술 스택 (제안)

> Vibe Idea Gen이 추천한 형태(PWA)에 맞춰 사용자가 직접 결정.
> 기존 레포의 패턴 참고할 것.

## 코딩 규약

- 경로: `pathlib.Path` 필수 (Windows 호환)
- 한국어 주석 OK
- 작은 샘플로 먼저 테스트
