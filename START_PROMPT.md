# Claude Code 시작 프롬프트 가이드

> 이 파일은 사용자용 가이드입니다. Claude Code 첫 세션에 어떻게 컨텍스트를 전달할지 안내.

---

## 사전 준비 (5분)

1. **Claude Code 설치 확인**
   ```powershell
   claude --version
   ```

2. **프로젝트 폴더 생성**
   ```powershell
   cd C:\Projects     # 또는 원하는 위치
   mkdir vibe-idea-gen
   cd vibe-idea-gen
   ```

3. **핸드오프 파일 배치**
   - `HANDOFF.md`, `CLAUDE.md`, `ROADMAP.md` → 프로젝트 루트
   - `project-files/` 안의 모든 파일 → 프로젝트 루트로 옮기기
     (`pyproject.toml`, `.env.example`, `.gitignore`, `README.md`, `src/` 폴더 통째로)

4. **Claude Code 실행**
   ```powershell
   claude
   ```

---

## 첫 메시지 (복사해서 붙여넣기)

다음 메시지를 그대로 첫 입력으로 사용하세요:

```
프로젝트 폴더에 HANDOFF.md, CLAUDE.md, ROADMAP.md가 있습니다. 
이 세 파일을 모두 읽고 프로젝트 컨텍스트를 파악해주세요.

읽고 나면 다음 작업을 진행해줘:

1. 현재 프로젝트 폴더의 파일 구조를 확인
2. uv가 설치되어 있는지 점검 (없으면 설치 안내)
3. uv sync로 의존성 설치
4. .env.example을 보고 .env 파일 생성을 도와줘 
   (GitHub Token은 내가 직접 입력)
5. ROADMAP.md의 Phase 1 검증 작업을 함께 진행

참고: 나는 한국어로 답변 받기를 선호하고, 간결한 응답을 원해요.
설명보다는 동작하는 코드와 실행 결과 우선.
```

---

## 두 번째 단계 (Phase 1 검증 후)

`vibe collect`와 `vibe stats`가 정상 동작하면 다음 메시지:

```
Phase 1 검증 완료. stats 결과는 [캡처/요약 붙여넣기]

이제 ROADMAP.md의 Phase 2를 시작하고 싶어. 
"설계 결정 필요" 항목들을 먼저 함께 검토하고, 
확정되면 src/llm.py와 src/analyze.py 작성에 들어가자.
```

---

## 세션 중 자주 쓸 명령

Claude Code 안에서:

| 의도 | 명령 |
|---|---|
| 파일 확인 | `cat <파일>` 또는 그냥 "X 파일 보여줘" |
| 코드 변경 | "X.py에서 Y 함수를 Z로 수정해줘" |
| 실행 | "uv run vibe collect 실행하고 결과 보여줘" |
| 디버깅 | "방금 에러 메시지 분석하고 수정해줘" |
| 진행 추적 | "ROADMAP.md의 체크박스 업데이트해줘" |

---

## 핸드오프 파일 역할 정리

| 파일 | 역할 | Claude가 언제 읽음 |
|---|---|---|
| **HANDOFF.md** | 첫 세션 풀 컨텍스트 (한 번만 필요) | 첫 메시지로 명시적 요청 |
| **CLAUDE.md** | 프로젝트 상시 참조 (간결) | 매 세션 자동 |
| **ROADMAP.md** | 단계별 체크리스트 + 진행 추적 | 작업 진행 시마다 |

---

## 트러블슈팅

### Claude Code가 컨텍스트를 잊는 것 같으면
"CLAUDE.md 다시 읽고 작업 계속해줘"

### 새로운 결정사항이 생기면
"이거 ROADMAP.md의 미해결 질문 섹션에 기록해줘"

### Phase 전환 시
"Phase 2 시작 전에 ROADMAP.md의 Phase 2 설계 결정 항목 검토하자"

---

## 팁

1. **핸드오프 파일은 git에 같이 커밋**해두면 다른 PC에서도 동일 컨텍스트로 작업 가능
2. **세션이 길어지면** 중간에 "지금까지 한 작업을 ROADMAP.md에 반영해줘" 한 번 요청
3. **새 Phase 시작 시** 항상 사용자 검토 받기 (CLAUDE.md에 명시되어 있음)
4. **막히는 부분**은 차라리 Claude.ai에서 설계 논의 후 결정사항만 Claude Code에 전달
