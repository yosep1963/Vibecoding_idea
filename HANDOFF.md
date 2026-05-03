# Vibe Idea Generator — Claude Code 핸드오프

> Claude Code 첫 세션 시작 시 이 파일을 읽혀 컨텍스트를 한 번에 주입한다.
> 사용법: `claude` 실행 후 첫 메시지로 "이 파일 읽고 작업 시작해줘: HANDOFF.md"

---

## 1. 사용자 정보 (반드시 인지)

| 항목 | 내용 |
|---|---|
| 이름 | 장창형 (Changhyeong) |
| 직업 | 대구가톨릭대학교 의과대학 소화기내과 교수 (간장학 전공, 임상 30년차) |
| 정년 | 2028년 8월 예정 |
| 개발 스타일 | Vibe coding (Claude Code 적극 활용), 임상 AI + 풀스택이 주력 |
| 진행 중 프로젝트 | AsterixisNet (CLINICCAI 2026 목표), TodoList 풀스택 앱 |
| 한국어 응답 선호 | 예 |
| 응답 톤 | 간결하고 핵심 위주, 단 기술 설명은 단계별로 상세히 |

**중요**: 의대 교수이자 임상 AI 연구자라는 컨텍스트를 모든 추천/분석에 반영할 것.

---

## 2. 프로젝트 한 줄 요약

> **본인의 GitHub 레포 + 작업 패턴을 데이터로 분석해서, "다음에 만들 만한 프로젝트 3개"를 추천하는 메타 도구.**

핵심 가치: 매번 새 프로젝트 시작할 때 "뭘 만들지" 고민을 줄임. 단순 아이디어 나열이 아니라 **본인의 실제 빈틈**을 데이터로 보여줌.

---

## 3. 실행 환경 (확정)

| 항목 | 사양 |
|---|---|
| OS | Windows 11 |
| CPU | AMD Threadripper 2950X (16C/32T) |
| RAM | 32GB DDR4 |
| GPU | RTX 3090 Ti (24GB VRAM) ← 로컬 임베딩/LLM 활용 |
| Python | 3.11+ (uv로 관리) |
| 운용 방식 | 24/7 아님. 퇴근 후 필요할 때만 실행 (월 1-2회 예상) |

**왜 Windows + 3090 Ti**: 평소 퇴근 후 쓰는 PC라 자연스럽고, 3090 Ti로 로컬 임베딩/LLM 돌리면 Claude API 비용 거의 zero + 본인 데이터 외부 전송 안 됨.

---

## 4. 기술 스택 (확정)

```
백엔드:    Python 3.11 + FastAPI (필요시) / 우선은 CLI
DB:        SQLite (로컬, 단일 사용자)
LLM:       
  - 로컬:  Ollama (nomic-embed-text 임베딩, qwen2.5:14b 1차 분석)
  - API:   Claude API (Sonnet 4.6) — 최종 추천에만 사용
시각화:    UMAP + scikit-learn (Phase 2), 추후 D3 (선택)
CLI:       typer + rich
패키징:    uv
```

**핵심 원칙**: 로컬 우선, Claude API는 품질 중요한 마지막 단계에만.

---

## 5. 4단계 개발 로드맵

### Phase 1: 데이터 수집 ✅ (이미 프로토타입 작성됨)
- GitHub API로 본인 레포 메타데이터 + README + 의존성 파일 수집
- SQLite 저장
- CLI: `vibe collect`, `vibe stats`, `vibe show`

### Phase 2: 분석 레이어 (다음 작업)
- Ollama로 각 레포 임베딩 (`nomic-embed-text`)
- 로컬 LLM(Qwen 2.5 14B)으로 카테고리 자동 태깅 (도메인/형태/상태)
- UMAP 차원 축소 → HDBSCAN 클러스터링
- CLI: `vibe analyze`

### Phase 3: 추천 생성
- 빈틈 추론 (어느 영역이 비어있는지 LLM으로 분석)
- Claude API로 최종 프로젝트 3개 제안
- 각 추천에 CLAUDE.md 초안 + 재사용 자산 표시
- CLI: `vibe recommend`

### Phase 4 (선택): 자기개선 루프
- 추천 → 실제 만든 것 추적
- 사용자 피드백 학습

---

## 6. 디렉토리 구조 (현재)

```
vibe-idea-gen/
├── CLAUDE.md              # Claude Code가 자동 참조
├── HANDOFF.md             # 이 파일 (첫 세션용)
├── ROADMAP.md             # 단계별 체크리스트
├── README.md              # 사용자용 문서
├── pyproject.toml         # uv 설정
├── .env                   # API 키 (gitignore)
├── .env.example
├── .gitignore
├── data/
│   └── repos.db           # SQLite (gitignore)
└── src/
    ├── __init__.py
    ├── main.py            # CLI 엔트리 (typer)
    ├── config.py          # 환경 설정
    ├── models.py          # SQLAlchemy 모델
    ├── collect.py         # ✅ Phase 1 완료
    ├── analyze.py         # ⏳ Phase 2 (다음 작업)
    ├── recommend.py       # ⏳ Phase 3
    └── llm.py             # Claude/Ollama 래퍼
```

---

## 7. 데이터 모델 요약

```python
# repos: GitHub 메타데이터
id, name, full_name, description, language, topics(JSON),
stars, forks, is_fork, is_archived,
created_at, pushed_at, readme, package_files(JSON),
fetched_at

# analysis: Phase 2 결과 (1:1 with repos)
repo_id, domain, form, status,
embedding(BLOB), cluster_id, analyzed_at

# recommendations: Phase 3 결과 이력
id, generated_at, payload(JSON), acted_on(JSON)
```

---

## 8. 설계 원칙 (절대 잊지 말 것)

1. **단계별 독립 실행** — 각 Phase는 캐시된 결과 활용. Phase 2를 100번 돌려도 GitHub 다시 안 부름
2. **로컬 우선** — 임베딩/1차 분류는 Ollama, 최종 추천만 Claude API
3. **사용자 컨텍스트 항상 주입** — 모든 LLM 호출에 "간장학 교수" 정보 포함
4. **결과 추적 가능** — 모든 추천 결과 DB 저장 (회고 가능)
5. **재실행 안전** — upsert 방식, 여러 번 돌려도 중복/오류 없음

---

## 9. 보안/프라이버시

- `.env`는 절대 커밋 금지
- GitHub PAT는 read 권한만
- 본인 GitHub 데이터 → Claude API 보낼 때 요약본만 (전체 README 안 보냄)
- Ollama 로컬 임베딩으로 README 내용 외부 유출 방지

---

## 10. 이미 작성된 파일 (재사용)

다음 파일들은 이미 작성 완료. Claude Code 작업 시작 시 그대로 사용:

- `CLAUDE.md` — 프로젝트 컨텍스트 (Claude Code 자동 참조)
- `pyproject.toml` — uv 의존성
- `.env.example` — 환경변수 템플릿
- `.gitignore`
- `src/__init__.py`
- `src/config.py` — 설정 로드
- `src/models.py` — SQLAlchemy 모델 3개
- `src/collect.py` — Phase 1 완전 구현 (비동기 GitHub API + retry + rate limit 대응)
- `src/main.py` — typer CLI (collect, stats, show)
- `README.md` — 사용자 가이드

→ **Claude Code 첫 작업**: 위 파일들을 받아서 프로젝트 폴더에 배치 후, `uv sync`로 환경 구축, `vibe collect` 실행 검증.

---

## 11. 첫 세션 권장 작업 순서

```
1. uv sync                          # 의존성 설치
2. .env 작성 (GITHUB_TOKEN 발급)
3. uv run vibe collect              # Phase 1 실행 검증
4. uv run vibe stats                # 본인 데이터 확인
5. → 결과 보고 Phase 2 설계 시작
```

**Claude Code에게**: 위 1-4번이 정상 동작하는지 먼저 확인. 에러 나면 디버깅 우선.
4번 결과를 기반으로 Phase 2 설계를 사용자와 함께 다듬을 것.

---

## 12. Phase 2 설계 시 주의점 (미리 인지)

Phase 2 시작 시 다음을 고려할 것:

- **Ollama가 Windows에 설치되어 있는지** 먼저 확인 (`ollama list`)
- **모델 다운로드** 시간 고려: `nomic-embed-text` (~270MB), `qwen2.5:14b` (~9GB)
- **임베딩 입력 텍스트 구성**: README + description + topics + 주요 의존성 키워드를 결합. 너무 길면 잘라서.
- **클러스터 개수**: 본인 레포 N개에 따라 다름. HDBSCAN으로 자동 결정 vs k-means로 수동(예: 5-7개) 고민 필요.
- **카테고리 태깅 프롬프트**: "임상AI / 풀스택웹앱 / 인프라도구 / 학습용 / 취미" 등 본인 컨텍스트에 맞는 라벨 사전 정의.

---

## 13. Phase 3 설계 시 주의점 (미리 인지)

- **빈틈 추론 프롬프트의 핵심**: "뻔한 추천 금지". Todo 앱, 블로그 같은 일반 추천 명시적으로 배제.
- **컨텍스트 주입**: 매 호출마다 "간장학 교수 + 임상 AI + Windows/Mac/Ubuntu 멀티 환경 + 가족 구성(딸 유진, ML 백그라운드)" 명시.
- **출력 강제 형식**: 각 추천 = 한 줄 요약 + 소요시간 + 재사용 자산 + 새로 배울 것 + 의미.
- **Claude API 호출**: Sonnet 4.6 사용. 토큰 절약 위해 레포 데이터 요약본만 전달.

---

## 14. 알려진 미해결 질문 (사용자와 논의 필요)

작업 진행 중 다음 결정 필요. 마주칠 때 사용자에게 확인:

- [ ] Claude.ai 대화 export 데이터를 분석에 포함할지? (Phase 2/3에서 의미있는 시그널일 수 있으나 export 번거로움)
- [ ] 웹 대시보드 만들지? (UMAP 시각화 인터랙티브로 보고 싶다면 Next.js 추가)
- [ ] Phase 4 자기개선 루프를 실제로 구현할지? (없어도 도구는 충분히 유용)

---

## 15. Claude Code에게 — 행동 지침

1. **이 핸드오프를 다 읽었으면 요약하지 말고** 바로 작업 시작 가능 여부 확인 (`uv sync` 단계부터)
2. **에러 나면 사용자 컨텍스트 다시 확인** (Windows 경로, GPU 사용 여부 등)
3. **새 코드 작성 시** `CLAUDE.md`의 설계 원칙 위반 안 하는지 검증
4. **Phase 2/3 진입 전** 사용자에게 한 번 설계 검토 요청
5. **사용자가 한국어로 질문** → 한국어로 답변 (코드 주석도 한국어 OK)
6. **사용자 시간 절약 우선** — 긴 설명보다 동작하는 코드 우선

---

끝.
