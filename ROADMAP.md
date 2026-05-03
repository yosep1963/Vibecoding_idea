# ROADMAP.md

> Vibe Idea Generator 단계별 작업 계획 + 체크리스트.
> Claude Code는 작업 진행 상황을 이 파일에서 추적한다.

---

## Phase 0: 환경 셋업

- [ ] Windows PC에 Python 3.11+ 설치 확인
- [ ] uv 설치 (`winget install astral-sh.uv`)
- [ ] Ollama for Windows 설치 (https://ollama.com)
- [ ] Ollama 모델 다운로드:
  ```
  ollama pull nomic-embed-text     # ~270MB
  ollama pull qwen2.5:14b          # ~9GB
  ```
- [ ] GitHub Personal Access Token 발급 (read 권한)
- [ ] Anthropic API 키 확보 (Phase 3에서 사용)
- [ ] 프로젝트 폴더 생성 + 파일 배치
- [ ] `uv sync` 실행
- [ ] `.env` 작성

**완료 기준**: `uv run vibe --help`가 정상 출력됨.

---

## Phase 1: 데이터 수집 ✅ (코드 작성 완료)

### 작성된 파일
- `src/config.py` ✅
- `src/models.py` ✅
- `src/collect.py` ✅
- `src/main.py` ✅

### 검증 작업 (Claude Code 첫 작업)
- [ ] `uv run vibe collect` 실행 → 에러 없이 완료
- [ ] `uv run vibe stats` → 본인 레포 N개 표시 확인
- [ ] `uv run vibe show <레포명>` → 상세 정보 확인
- [ ] README 수집률 점검 (대부분 레포에서 README 보유 확인)
- [ ] CLAUDE.md 보유 레포 개수 확인 (vibe coding 패턴 시그널)

### 알려진 한계 / 추후 개선
- [ ] private 레포 포함 옵션 추가 (현재는 public/private 모두)
- [ ] 커밋 메시지 분석 (현재 미구현 — 추후 Phase 2에서?)
- [ ] organization 레포 옵션 (현재 owner=본인 만)

**완료 기준**: SQLite에 본인 레포 데이터가 모두 저장되고, `stats` 출력이 합리적.

---

## Phase 2: 분석 레이어 ⏳ (다음 작업)

### 목표
각 레포를 임베딩 + 카테고리 태깅 + 클러스터링.

### 작업 순서

#### 2.1 LLM 래퍼 (`src/llm.py`)
- [ ] Ollama 클라이언트 (임베딩 + 채팅)
- [ ] Claude API 클라이언트 (Phase 3에서 사용하지만 미리 작성)
- [ ] 공통 인터페이스 (옵션 — 너무 추상화는 피할 것)

#### 2.2 임베딩 (`src/analyze.py` 일부)
- [ ] 각 레포의 임베딩용 텍스트 생성 함수
  - description + topics + README 앞부분 + 주요 의존성 키워드 결합
  - 토큰 길이 제한 처리
- [ ] Ollama로 임베딩 생성 (`nomic-embed-text`)
- [ ] numpy array를 BLOB으로 SQLite 저장
- [ ] 재실행 시 이미 임베딩된 레포는 스킵

#### 2.3 카테고리 태깅 (`src/analyze.py` 일부)
- [ ] 사전 정의 라벨 시스템
  ```python
  DOMAINS = ["임상AI", "풀스택웹앱", "인프라도구", "학습용", "취미", "기타"]
  FORMS = ["웹앱", "CLI", "라이브러리", "PWA", "노트북", "기타"]
  STATUSES = ["active", "archived", "abandoned"]
  ```
- [ ] 로컬 LLM(Qwen 2.5 14B)으로 분류 프롬프트
- [ ] 사용자 컨텍스트 주입 (의대 교수, 간장학)
- [ ] 결과를 `analysis` 테이블에 저장

#### 2.4 클러스터링
- [ ] UMAP으로 임베딩 차원 축소 (768D → 2D)
- [ ] HDBSCAN 또는 k-means로 클러스터링
- [ ] 클러스터 ID를 `analysis` 테이블에 저장
- [ ] (선택) 시각화 — matplotlib로 PNG 출력 또는 추후 D3

#### 2.5 CLI 명령
- [ ] `vibe analyze` — 전체 분석 파이프라인 실행
- [ ] `vibe analyze --rerun` — 캐시 무시하고 재분석
- [ ] `vibe clusters` — 클러스터별 레포 목록 출력

### 설계 결정 필요 (사용자와 논의)
- [ ] 클러스터 개수: 자동(HDBSCAN) vs 수동(k=5-7)?
- [ ] 임베딩 모델: `nomic-embed-text` vs `bge-m3`?
- [ ] 카테고리 라벨: 위 정의로 충분한지, 더 세분화 필요한지?

**완료 기준**: 본인 레포 N개가 모두 분류되고, 클러스터별로 의미있는 그룹이 보임.

---

## Phase 3: 추천 생성 ⏳

### 목표
빈틈 분석 + 다음 프로젝트 3개 추천 + CLAUDE.md 초안 자동 생성.

### 작업 순서

#### 3.1 빈틈 분석 (`src/recommend.py` 일부)
- [ ] 클러스터별 통계 (개수, 최근성, 활성도)
- [ ] 빈 영역 식별 (어느 도메인×형태 조합이 비어있는지 매트릭스)
- [ ] 로컬 LLM으로 1차 후보 생성 (10-20개)

#### 3.2 Claude API 추천 정제
- [ ] 사용자 컨텍스트 + 빈틈 데이터 + 후보 → Claude에게 전달
- [ ] Sonnet 4.6으로 최종 3개 추천
- [ ] 출력 형식 강제: 한 줄 요약 / 소요시간 / 재사용 자산 / 새로 배울 것 / 의미
- [ ] 결과를 `recommendations` 테이블에 저장

#### 3.3 CLAUDE.md 초안 생성
- [ ] 추천된 각 프로젝트에 대해 CLAUDE.md 템플릿 자동 생성
- [ ] 본인 컨텍스트 자동 주입
- [ ] 기존 자산 활용 가이드 포함
- [ ] `output/<프로젝트명>/CLAUDE.md` 형태로 저장

#### 3.4 CLI 명령
- [ ] `vibe recommend` — 추천 생성
- [ ] `vibe recommend --history` — 과거 추천 이력 보기
- [ ] `vibe recommend --mark-acted <id>` — "이거 만들었음" 표시

### 설계 결정 필요
- [ ] 추천 개수 고정(3) vs 가변?
- [ ] 빈틈 분석을 로컬 LLM이 할지, Claude가 할지?
- [ ] CLAUDE.md 초안에 boilerplate 코드도 포함할지?

**완료 기준**: 3개 추천이 출력되고, 각각이 본인 컨텍스트에 부합하며, CLAUDE.md 초안이 그대로 새 프로젝트 시작에 쓸 만함.

---

## Phase 4 (선택): 자기개선 루프

### 목표
추천 → 실제 만든 것 추적 → 다음 추천 가중치에 반영.

### 작업 순서
- [ ] `vibe recommend --mark-acted <id>` 명령으로 "만들었음" 표시
- [ ] 만든 프로젝트의 특징 분석 (어떤 추천이 실현됐나?)
- [ ] 다음 추천 시 사용자 선호 패턴 프롬프트에 주입
- [ ] (선택) "교수님은 백엔드 무거운 것보다 프론트 PWA를 더 자주 완성하시네요" 같은 메타 인사이트

**완료 기준**: 2-3회 사용 사이클 후 추천 품질이 첫 회보다 개선됨.

---

## 작업 진행 추적

### 현재 상태 (마지막 업데이트: 2026-05-03)

- ✅ Phase 1 코드 작성 완료
- ⏳ Phase 0 셋업 + Phase 1 실행 검증 (Claude Code 첫 작업)
- ⏳ Phase 2 설계 (검증 후 진행)

### 다음 단계

**즉시**: Windows PC에서 Phase 0 셋업 → Phase 1 실행 검증 → 결과 사용자와 함께 검토.

**그 다음**: 검토 결과 기반으로 Phase 2 세부 설계 확정 후 구현.

---

## 미해결 질문 (사용자 확인 대기)

- [ ] Claude.ai 대화 export 데이터 분석 포함 여부?
- [ ] 웹 대시보드(Next.js + UMAP 시각화) 만들지?
- [ ] Phase 4 자기개선 루프 실제 구현 여부?
- [ ] private 레포 포함 여부?
- [ ] organization 레포 포함 여부?

---

## 참고 자료

- 사용자 메모리: AsterixisNet, TodoList, OpenClaw, MCP 서버 활용 패턴
- Ollama 문서: https://ollama.com/library
- Anthropic API: https://docs.claude.com
- UMAP 공식: https://umap-learn.readthedocs.io
- HDBSCAN: https://hdbscan.readthedocs.io
