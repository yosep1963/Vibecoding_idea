# Vibe Idea Generator

본인의 GitHub 레포와 작업 패턴을 분석해서 다음 프로젝트를 추천하는 메타 도구.

## 빠른 시작

### 1. 환경 준비

```powershell
# uv 설치 (Windows PowerShell)
winget install astral-sh.uv

# 의존성 설치
cd vibe-idea-gen
uv sync
```

### 2. GitHub Token 생성

1. https://github.com/settings/tokens (classic) 접속
2. "Generate new token" → 권한: `repo` (read만 필요하지만 classic은 묶음)
   - 더 안전하게: Fine-grained token으로 본인 레포만 read 권한
3. 토큰 복사

### 3. 환경변수 설정

```powershell
# .env 파일 생성
copy .env.example .env
notepad .env
```

`.env` 내용:
```
GITHUB_TOKEN=ghp_여기에_토큰_붙여넣기
GITHUB_USERNAME=본인_깃허브_아이디
```

### 4. 실행

```powershell
# Phase 1: GitHub 레포 수집
uv run vibe collect

# 결과 확인
uv run vibe stats

# 특정 레포 상세 보기
uv run vibe show TodoList
```

## 옵션

```powershell
# fork한 레포도 포함
uv run vibe collect --include-forks

# archive된 레포도 포함
uv run vibe collect --include-archived
```

## 다음 단계

Phase 1 완료 후 Phase 2(분석), Phase 3(추천)이 추가될 예정.
자세한 내용은 [CLAUDE.md](./CLAUDE.md) 참조.
