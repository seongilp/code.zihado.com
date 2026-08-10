"""경로 상수와 ~/.env 파싱. 두 진입점이 공유한다."""

from __future__ import annotations

from pathlib import Path

STATE_DIR = Path.home() / ".local" / "state" / "threads-poster"
ENV_PATH = Path.home() / ".env"
LOG_PATH = Path.home() / "Library" / "Logs" / "threads-poster.log"
CLAUDE_PATH = Path.home() / ".local" / "bin" / "claude"

# scripts/threads/poster/config.py → 저장소 루트
REPO_ROOT = Path(__file__).resolve().parents[3]
PROJECTS_JSON = REPO_ROOT / "projects.json"
PROMPT_PATH = REPO_ROOT / "scripts" / "threads" / "compose-prompt.md"


class MissingCredentialError(RuntimeError):
    """~/.env 에 필요한 값이 없다."""


def load_dotenv(path: Path | str = ENV_PATH) -> dict[str, str]:
    """~/.env 의 KEY=VALUE 를 읽는다. 셸 문법 전체를 지원하지는 않는다."""
    target = Path(path)
    if not target.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in target.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export ") :].lstrip()
        key, _, value = line.partition("=")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[key.strip()] = value
    return values


def load_telegram_credentials(path: Path | str = ENV_PATH) -> tuple[str, str]:
    env = load_dotenv(path)
    token = env.get("TELEGRAM_BOT_TOKEN")
    chat_id = env.get("AUTHORIZED_CHAT_ID")
    if not token:
        raise MissingCredentialError("~/.env 에 TELEGRAM_BOT_TOKEN 이 없습니다")
    if not chat_id:
        raise MissingCredentialError("~/.env 에 AUTHORIZED_CHAT_ID 가 없습니다")
    return token, chat_id
