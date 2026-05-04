"""환경 설정 로드."""
from pathlib import Path
from dotenv import load_dotenv
import os

# 프로젝트 루트
ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

# .env 로드
load_dotenv(ROOT / ".env")


class Config:
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
    GITHUB_USERNAME: str = os.getenv("GITHUB_USERNAME", "")
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")

    DB_PATH: Path = DATA_DIR / "repos.db"
    DB_URL: str = f"sqlite:///{DB_PATH}"

    @classmethod
    def validate(cls, *, require_claude: bool = False) -> None:
        """필수 설정 확인. Phase에 따라 다른 키가 필요."""
        if not cls.GITHUB_TOKEN:
            raise ValueError(
                "GITHUB_TOKEN이 설정되지 않았습니다. .env 파일을 확인하세요."
            )
        if not cls.GITHUB_USERNAME:
            raise ValueError(
                "GITHUB_USERNAME이 설정되지 않았습니다. .env 파일을 확인하세요."
            )
        if require_claude:
            # Claude Agent SDK는 (1) CLAUDE_CODE_OAUTH_TOKEN 환경변수 또는
            # (2) `claude setup-token`으로 저장된 ~/.claude/.credentials.json 사용.
            oauth_token = os.getenv("CLAUDE_CODE_OAUTH_TOKEN", "")
            creds_file = Path.home() / ".claude" / ".credentials.json"
            if not oauth_token and not creds_file.exists():
                raise ValueError(
                    "Claude 인증 없음. 다음 중 하나 실행:\n"
                    "  (1) claude setup-token  (브라우저 OAuth → 영구 저장, 권장)\n"
                    "  (2) .env에 CLAUDE_CODE_OAUTH_TOKEN=... 추가"
                )


config = Config()
