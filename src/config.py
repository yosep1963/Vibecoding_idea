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
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")

    DB_PATH: Path = DATA_DIR / "repos.db"
    DB_URL: str = f"sqlite:///{DB_PATH}"

    @classmethod
    def validate(cls, *, require_anthropic: bool = False) -> None:
        """필수 설정 확인. Phase에 따라 다른 키가 필요."""
        if not cls.GITHUB_TOKEN:
            raise ValueError(
                "GITHUB_TOKEN이 설정되지 않았습니다. .env 파일을 확인하세요."
            )
        if not cls.GITHUB_USERNAME:
            raise ValueError(
                "GITHUB_USERNAME이 설정되지 않았습니다. .env 파일을 확인하세요."
            )
        if require_anthropic and not cls.ANTHROPIC_API_KEY:
            raise ValueError(
                "ANTHROPIC_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요."
            )


config = Config()
