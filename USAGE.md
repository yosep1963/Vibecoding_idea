# USAGE.md — Vibe Idea Generator 사용 가이드

> 일상 사용 방법, 운영 리듬, 트러블슈팅. 최초 설치는 `README.md` 참조.

## 0. 매번 사용 전 (PowerShell 셋업)

```powershell
cd D:\Claude_Workspace\Vibecoding_idea\vibe-idea-gen
. .\. .\setup.ps1
```

`setup.ps1`이 PATH(uv, Ollama) + UTF-8 인코딩을 한 번에 설정합니다.

수동으로 하려면

```powershell
$env:Path = "C:\Users\chlee\.local\bin;C:\Users\chlee\AppData\Local\Programs\Ollama;$env:Path"
$env:PYTHONIOENCODING = "utf-8"
chcp 65001
```

## 1. 일상 사용 시나리오 — "다음 뭐 만들지?"

월 1–2회, 새 프로젝트 시작이 고민될 때:

```powershell
uv run vibe collect      # 최근 GitHub 활동 반영 (~3분)
uv run vibe analyze      # 임베딩 + 클러스터 갱신 (~5분, GPU 사용)
uv run vibe recommend    # Claude로 추천 3개 + CLAUDE.md 초안 (~30초, ~$0.1)
```

`output\<추천명>\CLAUDE.md`가 생성됩니다. 마음에 드는 추천이 있으면

```powershell
mkdir C:\Projects\hepatox-notebook
copy output\hepatox-notebook\CLAUDE.md C:\Projects\hepatox-notebook\
cd C:\Projects\hepatox-notebook
claude          # Claude Code 실행 → CLAUDE.md를 자동 참조하여 바로 작업 시작
```

## 2. 데이터 탐색 명령

| 명령 | 출력 |
|---|---|
| `uv run vibe stats` | 언어 분포, 최근 push Top 10, README/CLAUDE.md 보유율 |
| `uv run vibe clusters` | 6개 클러스터별 레포 그룹 (작업 패턴 가시화) |
| `uv run vibe show <레포명>` | 특정 레포 상세 (예: `vibe show Voice-SOAP`) |
| `uv run vibe recommend --history` | 과거 추천 기록 (rec_id별) |

## 3. 단계별 재실행 옵션

| 명령 | 언제 사용 |
|---|---|
| `vibe collect` | GitHub에 새 레포 추가 / 푸시 후 |
| `vibe collect --include-forks` | fork 레포까지 분석에 포함 |
| `vibe collect --include-archived` | archive된 레포까지 포함 |
| `vibe analyze` | collect 후 (새 레포만 임베딩, 기존은 스킵) |
| `vibe analyze --rerun` | 임베딩 모델/카테고리 라벨 변경 시 (전체 재계산) |
| `vibe analyze --k 8` | 클러스터 개수 조정 (기본 6) |
| `vibe recommend` | 여러 번 실행 가능, 매번 새 추천 + DB 저장 |

## 4. 권장 운영 리듬

- **주 1회** — `vibe collect` (가벼움, 데이터만 최신화)
- **월 1회** — `vibe analyze` + `vibe recommend` (새 시각으로 다음 프로젝트 결정)
- **분기 1회** — `vibe recommend --history` 보고 회고: "내가 추천 받고 실제 만든 게 뭐였지?"

## 5. 추천 품질을 높이는 팁

- `.env`의 GitHub PAT는 만료 전에 갱신 (만료 시 `collect` 단계에서 401)
- README 안 쓴 레포가 많으면 추천 정확도 떨어짐 — 자주 만지는 레포 5개 정도는 README 1줄이라도 추가하면 임베딩 품질이 확 올라감
- Claude API 비용은 1회 약 $0.05–0.20. 월 10회 돌려도 $1–2 수준
- 추천이 뻔하다 싶으면 `vibe analyze --rerun` 후 다시 `vibe recommend` — 캐시 무효화로 신선한 결과

## 6. 트러블슈팅

| 증상 | 해결 |
|---|---|
| `'vibe' is not recognized` | `uv sync` 다시 실행 |
| `'uv' is not recognized` | `setup.ps1` 다시 로드 (PATH 설정 안 됨) |
| `401 Unauthorized` (collect) | GitHub PAT 만료/revoke — 재발급 후 `.env` 갱신 |
| `Ollama 서버 응답 없음` (analyze) | 시작 메뉴에서 Ollama 데스크톱 앱 실행 |
| `Ollama 모델 'bge-m3' 미설치` | `ollama pull bge-m3` |
| `Ollama 모델 'qwen2.5:14b' 미설치` | `ollama pull qwen2.5:14b` |
| `ANTHROPIC_API_KEY 미설정` | `.env`에 `sk-ant-…` 키 입력 |
| Claude API 한도 초과 | <https://console.anthropic.com/settings/billing> 잔액 확인 |
| 한글 출력 깨짐 | `setup.ps1` 로드 안 됨 — `chcp 65001` + `$env:PYTHONIOENCODING="utf-8"` 확인 |

## 7. 핵심 산출물 위치

```
D:\Claude_Workspace\Vibecoding_idea\vibe-idea-gen\
├── data\repos.db              ← SQLite (모든 데이터 영구 저장, 백업 권장)
├── output\<추천명>\CLAUDE.md  ← 새 프로젝트 시드 파일
└── .env                       ← 토큰 (절대 커밋/공유 금지, .gitignore 확인)
```

`data\repos.db`만 백업해 두면 어디서든 복원 가능 (collect 결과 + analysis 결과 + recommendations 이력 모두 포함).

## 8. 테스트 실행 (개발 시)

코드 수정 후 회귀 확인:

```powershell
uv run pytest          # 31개 단위 테스트 (~1초, 외부 호출 없음)
uv run pytest -v       # 자세한 출력
uv run pytest tests/test_analyze.py  # 특정 파일만
```

테스트 범위:
- `tests/test_analyze.py` — 임베딩 텍스트 구성, 상태 휴리스틱, BLOB 라운드트립
- `tests/test_recommend.py` — 빈틈 매트릭스 계산, JSON 추출, 디렉토리명 안전화
- `tests/test_cli.py` — CLI 명령 등록 + `--help` 동작

검증 못 하는 것: GitHub/Ollama/Anthropic 실제 응답 → `vibe collect/analyze/recommend` 직접 실행으로 확인.

## 9. CLI 명령 전체 요약

```
vibe collect [--include-forks] [--include-archived]
vibe stats
vibe show <레포명>
vibe analyze [--rerun] [--k N]
vibe clusters
vibe recommend [--history]
```

도움말은 `vibe --help` 또는 `vibe <명령> --help`.
