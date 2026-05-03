# CLAUDE.md

> asterixis-pylib — Vibe Idea Generator가 생성한 초기 컨텍스트.

## 프로젝트

**asterixis-pylib** — AsterixisNet 손떨림 검출 파이프라인을 pip 설치 가능한 Python 라이브러리로 패키징

## 사용자 컨텍스트 (모든 LLM 호출에 주입)

- 직업: 대구가톨릭대학교 의과대학 소화기내과 교수 (간장학)
- 임상 30년차, 2028년 8월 정년
- 개발 스타일: Vibe coding, 임상 AI + 풀스택 웹앱이 주력
- 한국어 응답 선호

## 분류

- 도메인: 임상AI
- 형태: 라이브러리
- 예상 소요: 1개월+

## 재사용 자산

Asterixis, Asterixis_smartphone, asterixis-0414 세 레포의 신호처리 함수(가속도계 파싱, FFT 특징 추출, 분류 추론 코드) 를 src 레이아웃으로 통합; Voice-SOAP의 pyproject.toml 패키징 구조를 템플릿으로 재활용

## 새로 배울 것

PyPI 배포 워크플로(GitHub Actions + Trusted Publisher), semantic-release 버전 자동화

## 왜 의미있는가

임상AI+라이브러리 조합이 현재 완전 비어 있음(empty). Asterixis 관련 레포가 cluster_0에 4개나 몰려 있고 코드가 CLI 스크립트로 흩어진 상태. 논문 투고 시 '코드 재현 가능성' 요건 충족 및 타 기관 연구자가 pip install 한 줄로 재현할 수 있게 되면 피인용 경로가 열림.

## 첫 PR 단계

1. 세 Asterixis 레포의 공통 함수 목록 추출 후 asterixisnet/core.py에 통합, 중복 제거
2. pyproject.toml에 [project] 메타데이터 + 의존성 명시, TestPyPI 업로드 확인
3. GitHub Actions CI: pytest + twine check 통과 후 태그 푸시 시 PyPI 자동 배포

## 기술 스택 (제안)

> Vibe Idea Gen이 추천한 형태(라이브러리)에 맞춰 사용자가 직접 결정.
> 기존 레포의 패턴 참고할 것.

## 코딩 규약

- 경로: `pathlib.Path` 필수 (Windows 호환)
- 한국어 주석 OK
- 작은 샘플로 먼저 테스트
