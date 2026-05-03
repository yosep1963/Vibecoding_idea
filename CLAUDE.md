# CLAUDE.md

> 이 파일은 Claude Code가 프로젝트 작업 시 항상 자동으로 참조한다.
> 첫 세션 핸드오프는 `HANDOFF.md` 참조.
> 단계별 작업 계획은 `ROADMAP.md` 참조.

## 프로젝트

**Vibe Idea Generator** — 본인 GitHub 레포 + 작업 패턴 기반 다음 프로젝트 추천 메타 도구.

## 사용자 컨텍스트 (모든 LLM 호출에 주입)

- 직업: 대구가톨릭대학교 의과대학 소화기내과 교수 (간장학)
- 임상 30년차, 2028년 8월 정년
- 개발 스타일: Vibe coding, 임상 AI + 풀스택 웹앱이 주력
- 진행 중: AsterixisNet (CLINICCAI 2026), TodoList 앱
- 한국어 응답 선호

## 실행 환경

- Windows 11 + Threadripper 2950X + RTX 3090 Ti (24GB VRAM) + 32GB RAM
- Python 3.11+, uv로 관리
- 24/7 운영 아님. 배치형. 월 1-2회 사용.

## 기술 스택

```
백엔드:  Python 3.11 + 우선 CLI (typer + rich)
DB:      SQLite (단일 사용자, 로컬)
LLM:     Ollama (로컬, 임베딩+1차분석) + Claude API (최종 추천만)
분석:    UMAP + scikit-learn
패키징:  uv
```

## 핵심 설계 원칙

1. **단계별 독립 실행** — 각 Phase는 캐시된 결과 활용. 재실행 비용 zero.
2. **로컬 우선** — 임베딩/1차 분류는 Ollama. Claude API는 최종 추천에만.
3. **사용자 컨텍스트 항상 주입** — 모든 LLM 프롬프트에 "간장학 교수" 명시.
4. **결과 추적 가능** — 추천 결과 DB 저장. 회고 가능.
5. **재실행 안전** — upsert, 여러 번 돌려도 안전.

## 디렉토리 구조

```
vibe-idea-gen/
├── CLAUDE.md, HANDOFF.md, ROADMAP.md, README.md
├── pyproject.toml, .env, .env.example, .gitignore
├── data/repos.db
└── src/
    ├── __init__.py, main.py, config.py, models.py
    ├── collect.py     # Phase 1 ✅
    ├── analyze.py     # Phase 2 ⏳
    ├── recommend.py   # Phase 3 ⏳
    └── llm.py         # LLM 래퍼
```

## 데이터 모델

```python
# repos
id, name, full_name, description, language, topics(JSON),
stars, forks, is_fork, is_archived,
created_at, pushed_at, readme, package_files(JSON), fetched_at

# analysis (Phase 2)
repo_id, domain, form, status, embedding(BLOB), cluster_id, analyzed_at

# recommendations (Phase 3)
id, generated_at, payload(JSON), acted_on(JSON)
```

## CLI 명령

```
vibe collect [--include-forks] [--include-archived]   # Phase 1
vibe stats                                            # 데이터 요약
vibe show <레포명>                                    # 상세 보기
vibe analyze                                          # Phase 2 (예정)
vibe recommend                                        # Phase 3 (예정)
```

## 코딩 규약

- **경로**: `pathlib.Path` 필수 (Windows 호환)
- **비동기**: GitHub API 등 I/O는 `httpx.AsyncClient`
- **에러 핸들링**: rate limit / 404 / 네트워크 오류 명시적 처리
- **로깅**: `rich.console` 사용
- **타입 힌트**: 모든 public 함수에 명시
- **주석**: 한국어 OK
- **Async semaphore**: 외부 API 동시성 제한 (예: 5)
- **데이터 자르기**: README 20KB, 의존성 파일 5KB 제한

## LLM 프롬프트 작성 원칙

### 임베딩 (로컬)
- 입력 = description + topics + README 첫 부분 + 주요 의존성 키워드
- 너무 긴 README는 잘라서 토큰 절약

### 카테고리 태깅 (로컬 LLM)
- 사전 정의 라벨: 임상AI / 풀스택웹앱 / 인프라도구 / 학습용 / 취미 / 기타
- 형태: 웹앱 / CLI / 라이브러리 / PWA / 노트북 / 기타
- 상태: active / archived / abandoned (마지막 push + README 완성도 기반)

### 빈틈 추론 (Claude API)
- ❌ "이 사용자에게 어울리는 프로젝트 추천해주세요"
- ✅ "다음 N개 프로젝트의 패턴을 보고, 만들 법한데 안 만든 영역 식별. 의대 교수+간장학 컨텍스트 무시하지 말 것. 뻔한 추천(Todo 앱 등) 제외."

### 추천 출력 강제 형식
각 추천은 반드시 다음 모두 포함:
- 한 줄 요약
- 예상 소요 시간 (주말 / 1-2주 / 1개월+)
- 기존 자산 재활용 (어느 레포의 어느 부분?)
- 새로 배워야 할 것 (1-2개만)
- 왜 의미있는가 (의사+간장학 컨텍스트에서)

## 보안

- `.env` 절대 커밋 금지
- GitHub PAT는 read 권한만
- 본인 데이터 → Claude API 보낼 때 요약본만
- Ollama 로컬 임베딩으로 README 외부 유출 방지

## 작업 시작 전 체크리스트

새 Phase 시작할 때:
- [ ] 사용자에게 설계 한 번 보여주고 검토 요청
- [ ] 기존 데이터 모델 확장 필요한지 확인
- [ ] 새로운 의존성은 `pyproject.toml`에 명시
- [ ] CLI 명령 추가는 `main.py`에 등록
- [ ] 테스트는 작은 샘플로 먼저 (전체 레포 돌리기 전)

## 디버깅 포인트

자주 마주칠 이슈:
- **GitHub rate limit** → `_request()`의 retry 로직 확인
- **Ollama 모델 미설치** → `ollama list`로 확인 후 `ollama pull`
- **Windows 인코딩** → `errors="replace"`로 README 디코딩
- **SQLite lock** → 세션 명시적으로 close
- **CUDA 사용 여부** → Ollama 자동 감지, 별도 설정 불필요
