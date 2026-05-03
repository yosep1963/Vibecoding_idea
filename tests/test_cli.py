"""CLI 스모크 테스트: --help 동작 + 모든 명령 등록 확인."""
from typer.testing import CliRunner

from src.main import app

runner = CliRunner()


def test_help_exits_cleanly():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0


def test_all_commands_registered():
    result = runner.invoke(app, ["--help"])
    output = result.stdout
    for cmd in ("collect", "stats", "show", "analyze", "clusters", "recommend"):
        assert cmd in output, f"명령 '{cmd}'가 --help 에 없음"


def test_each_command_has_help():
    for cmd in ("collect", "stats", "show", "analyze", "clusters", "recommend"):
        result = runner.invoke(app, [cmd, "--help"])
        assert result.exit_code == 0, f"'{cmd} --help' 실패"
