# Vibe Idea Generator 환경 셋업 스크립트
# 사용법: PowerShell에서 . .\setup.ps1   (점-공백-경로, dot-source 방식)
#
# 점-공백 방식으로 실행해야 환경변수가 현재 세션에 남습니다.
# `.\setup.ps1`로 실행하면 자식 셸에서만 적용되고 종료 시 사라집니다.

$uvBin = "C:\Users\chlee\.local\bin"
$ollamaBin = "C:\Users\chlee\AppData\Local\Programs\Ollama"

# PATH에 uv, Ollama 추가 (중복 방지)
if ($env:Path -notlike "*$uvBin*") {
    $env:Path = "$uvBin;$env:Path"
}
if ($env:Path -notlike "*$ollamaBin*") {
    $env:Path = "$ollamaBin;$env:Path"
}

# Python/Rich 한글 출력
$env:PYTHONIOENCODING = "utf-8"
chcp 65001 | Out-Null

# 헬스체크
Write-Host "=== Vibe Idea Generator 환경 ===" -ForegroundColor Cyan

$uv = Get-Command uv -ErrorAction SilentlyContinue
if ($uv) { Write-Host "  uv      : OK ($(& uv --version 2>&1 | Select-Object -First 1))" -ForegroundColor Green }
else     { Write-Host "  uv      : NOT FOUND" -ForegroundColor Red }

$ollama = Get-Command ollama -ErrorAction SilentlyContinue
if ($ollama) {
    Write-Host "  Ollama  : OK ($(& ollama --version 2>&1 | Select-Object -First 1))" -ForegroundColor Green
    try {
        $tags = Invoke-WebRequest -Uri 'http://localhost:11434/api/tags' -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
        $models = ($tags.Content | ConvertFrom-Json).models
        $needed = @('bge-m3', 'qwen2.5:14b')
        foreach ($n in $needed) {
            $found = $models | Where-Object { $_.name -eq $n -or $_.name -like "$n*" }
            if ($found) { Write-Host "  model   : $n  OK" -ForegroundColor Green }
            else        { Write-Host "  model   : $n  MISSING (run: ollama pull $n)" -ForegroundColor Yellow }
        }
    } catch {
        Write-Host "  Ollama server: NOT RUNNING (시작 메뉴에서 Ollama 실행)" -ForegroundColor Yellow
    }
} else {
    Write-Host "  Ollama  : NOT FOUND" -ForegroundColor Red
}

if (Test-Path .env) { Write-Host "  .env    : 있음" -ForegroundColor Green }
else                { Write-Host "  .env    : 없음 (cp .env.example .env 후 토큰 입력)" -ForegroundColor Red }

Write-Host ""
Write-Host "사용 가능 명령:" -ForegroundColor Cyan
Write-Host "  uv run vibe collect | stats | show <name> | analyze | clusters | recommend"
Write-Host "자세한 사용법: USAGE.md"
