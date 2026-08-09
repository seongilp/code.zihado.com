# Threads 일일 프로젝트 소개 자동 포스팅 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `projects.json`의 프로젝트를 매일 하나씩 골라 문구를 생성하고, 텔레그램 승인을 거쳐 Threads에 게시하는 시스템을 만든다.

**Architecture:** launchd 잡 두 개(08:00 초안 생성 / 5분마다 승인 폴링)가 Python 진입점을 호출한다. 로직은 `poster/` 패키지의 작은 모듈로 나뉘고, HTTP·subprocess는 전부 주입되어 네트워크 없이 테스트된다. 상태는 저장소 밖 `~/.local/state/threads-poster/`에 둔다.

**Tech Stack:** Python 3.13 (표준 라이브러리만), pytest 7.4, launchd, Threads Graph API v1.0, Telegram Bot API, headless `claude -p`

**설계 문서:** `docs/superpowers/specs/2026-08-09-threads-daily-poster-design.md`

---

## 설계 문서에서 달라진 점

구현하면서 확정한 두 가지 refinement. 설계의 의도는 그대로다.

1. **회차 전환 방식** — 설계는 "후보가 소진되면 `posted.json`을 비우고 2회차 시작"이라고 썼다.
   구현에서는 **기록을 비우지 않고 `round` 필드로 구분**한다. `round=1` 기록이 모든 프로젝트를
   덮으면 자동으로 `round=2` 후보군이 열린다. 2회차에서 1회차 본문을 참조해야 하므로
   기록을 지울 수 없다. `posted.json` 스키마는 설계 그대로다.

2. **모듈 이름** — 진입점 `compose.py`와 로직 모듈이 같은 이름이면 혼란스러우므로
   로직은 `poster/composer.py`로 둔다. 진입점 이름은 설계대로 `compose.py` / `approve.py`.

3. **`poster/config.py` 추가** — `~/.env` 파싱과 경로 상수를 담는다. 설계에 명시되지 않았지만
   두 진입점이 공유해야 하는 코드다.

---

## 파일 구조

```
scripts/threads/
  conftest.py             빈 파일 — pytest가 scripts/threads 를 sys.path 에 넣게 한다
  compose.py              진입점: 08:00 초안 생성
  approve.py              진입점: 5분마다 승인 폴링
  compose-prompt.md       claude -p 에 넘길 문구 작성 지침
  README.md               설치·운영·토큰 발급 절차
  poster/
    __init__.py
    config.py             ~/.env 파싱, 경로 상수
    state.py              상태 파일 읽기/쓰기, flock
    selector.py           후보 선택, 회차 계산
    sanitize.py           LLM 출력 정리, 길이 검증
    telegram.py           전송, getUpdates, 인라인 버튼
    threads_api.py        컨테이너 생성, 게시, 토큰 갱신
    composer.py           프롬프트 조립, claude 호출, 재시도
  tests/
    test_state.py
    test_selector.py
    test_sanitize.py
    test_telegram.py
    test_threads_api.py
    test_composer.py
    test_compose_entry.py
    test_approve_entry.py
  launchd/
    com.zihado.threads-compose.plist
    com.zihado.threads-approve.plist
```

**책임 경계**

- `selector` / `sanitize` — 순수 함수. 파일도 네트워크도 모른다
- `state` — 상태 파일에 닿는 유일한 경로. 잠금도 여기서만
- `telegram` / `threads_api` — HTTP만. 주입된 트랜스포트를 쓴다
- `composer` — 프롬프트 조립. 주입된 runner를 쓴다
- 진입점 2개 — 위를 조립하고 오류를 텔레그램으로 알린다

**테스트 실행 방법 (모든 태스크 공통)**

```bash
cd /Users/zihado/work/playground/code.zihado.com/scripts/threads && python3 -m pytest tests -v
```

---

## Task 1: 뼈대와 상태 저장소

**Files:**
- Create: `scripts/threads/conftest.py`
- Create: `scripts/threads/poster/__init__.py`
- Create: `scripts/threads/poster/state.py`
- Test: `scripts/threads/tests/test_state.py`

- [ ] **Step 1: 빈 파일 두 개를 만든다**

```bash
mkdir -p scripts/threads/poster scripts/threads/tests scripts/threads/launchd
touch scripts/threads/conftest.py scripts/threads/poster/__init__.py
```

`conftest.py`는 내용이 없어야 한다. pytest가 이 파일을 보고 `scripts/threads`를
`sys.path`에 넣어주기 때문에 테스트에서 `import poster`가 동작한다.

- [ ] **Step 2: 실패하는 테스트를 쓴다**

Create `scripts/threads/tests/test_state.py`:

```python
import json
import os

import pytest

from poster.state import LockBusy, State, exclusive_lock


def test_read_json_returns_default_when_missing(tmp_path):
    state = State(tmp_path)
    assert state.read_json("posted.json", []) == []


def test_write_then_read_roundtrip_keeps_korean(tmp_path):
    state = State(tmp_path)
    state.write_json("posted.json", [{"slug": "law", "text": "한글"}])
    assert state.read_json("posted.json", []) == [{"slug": "law", "text": "한글"}]


def test_write_json_is_atomic_and_leaves_no_temp_files(tmp_path):
    state = State(tmp_path)
    state.write_json("posted.json", [{"slug": "law"}])
    leftovers = [p.name for p in tmp_path.iterdir() if p.name.startswith(".")]
    assert leftovers == []


def test_write_json_private_sets_owner_only_permissions(tmp_path):
    state = State(tmp_path)
    state.write_json("token.json", {"token": "secret"}, private=True)
    mode = os.stat(tmp_path / "token.json").st_mode & 0o777
    assert mode == 0o600


def test_delete_is_idempotent(tmp_path):
    state = State(tmp_path)
    state.delete("pending.json")  # 없어도 예외가 나지 않는다
    state.write_json("pending.json", {"slug": "law"})
    state.delete("pending.json")
    assert not (tmp_path / "pending.json").exists()


def test_second_lock_raises_lock_busy(tmp_path):
    with exclusive_lock(tmp_path):
        with pytest.raises(LockBusy):
            with exclusive_lock(tmp_path):
                pass


def test_lock_is_released_after_exit(tmp_path):
    with exclusive_lock(tmp_path):
        pass
    with exclusive_lock(tmp_path):
        pass  # 예외 없이 다시 잡힌다
```

- [ ] **Step 3: 테스트가 실패하는지 확인한다**

Run: `cd scripts/threads && python3 -m pytest tests/test_state.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'poster.state'`

- [ ] **Step 4: 최소 구현을 쓴다**

Create `scripts/threads/poster/state.py`:

```python
"""상태 파일에 닿는 유일한 경로. 잠금도 여기서만 건다."""

from __future__ import annotations

import fcntl
import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


class LockBusy(RuntimeError):
    """다른 인스턴스가 이미 상태 디렉토리를 잠갔다."""


class State:
    def __init__(self, state_dir: Path | str) -> None:
        self.dir = Path(state_dir)
        self.dir.mkdir(parents=True, exist_ok=True)

    def path(self, name: str) -> Path:
        return self.dir / name

    def read_json(self, name: str, default: Any) -> Any:
        target = self.path(name)
        if not target.exists():
            return default
        with target.open(encoding="utf-8") as handle:
            return json.load(handle)

    def write_json(self, name: str, value: Any, *, private: bool = False) -> None:
        """임시 파일에 쓰고 rename 한다. 중간에 죽어도 반쪽짜리 파일이 남지 않는다."""
        target = self.path(name)
        fd, tmp_name = tempfile.mkstemp(dir=self.dir, prefix=f".{name}.", suffix=".tmp")
        tmp = Path(tmp_name)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(value, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(tmp, 0o600 if private else 0o644)
            os.replace(tmp, target)
        except BaseException:
            tmp.unlink(missing_ok=True)
            raise

    def delete(self, name: str) -> None:
        self.path(name).unlink(missing_ok=True)


@contextmanager
def exclusive_lock(state_dir: Path | str) -> Iterator[None]:
    """겹쳐 실행되면 두 번째는 LockBusy 로 즉시 빠져나간다."""
    directory = Path(state_dir)
    directory.mkdir(parents=True, exist_ok=True)
    fd = os.open(directory / "lock", os.O_CREAT | os.O_RDWR, 0o600)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise LockBusy("다른 인스턴스가 실행 중입니다") from exc
        yield
    finally:
        os.close(fd)
```

- [ ] **Step 5: 테스트가 통과하는지 확인한다**

Run: `cd scripts/threads && python3 -m pytest tests/test_state.py -v`
Expected: PASS — 7 passed

- [ ] **Step 6: 커밋한다**

```bash
git add scripts/threads/conftest.py scripts/threads/poster/__init__.py \
        scripts/threads/poster/state.py scripts/threads/tests/test_state.py
git commit -m "feat: Threads 포스터 상태 저장소와 잠금"
```

---

## Task 2: 후보 선택과 회차 계산

**Files:**
- Create: `scripts/threads/poster/selector.py`
- Test: `scripts/threads/tests/test_selector.py`

- [ ] **Step 1: 실패하는 테스트를 쓴다**

Create `scripts/threads/tests/test_selector.py`:

```python
import random

import pytest

from poster.selector import NoProjectsError, UnknownSlugError, choose, flatten_projects


def catalog(*slugs):
    return {
        "categories": [
            {"id": "web", "projects": [{"slug": s, "name": s.upper()} for s in slugs]}
        ]
    }


def rng():
    return random.Random(42)


def test_flatten_projects_walks_every_category():
    data = {
        "categories": [
            {"id": "web", "projects": [{"slug": "a"}]},
            {"id": "cli", "projects": [{"slug": "b"}, {"slug": "c"}]},
        ]
    }
    assert [p["slug"] for p in flatten_projects(data)] == ["a", "b", "c"]


def test_choose_picks_from_projects_when_nothing_posted():
    selection = choose(catalog("a", "b"), [], rng=rng())
    assert selection.project["slug"] in {"a", "b"}
    assert selection.round == 1
    assert selection.previous_texts == ()


def test_choose_never_repeats_within_a_round():
    posted = [{"slug": "a", "round": 1}]
    selection = choose(catalog("a", "b"), posted, rng=rng())
    assert selection.project["slug"] == "b"


def test_skipped_projects_are_not_offered_again_in_the_same_round():
    posted = [{"slug": "a", "round": 1, "skipped": True}]
    selection = choose(catalog("a", "b"), posted, rng=rng())
    assert selection.project["slug"] == "b"


def test_round_advances_when_every_project_is_covered():
    posted = [{"slug": "a", "round": 1}, {"slug": "b", "round": 1}]
    selection = choose(catalog("a", "b"), posted, rng=rng())
    assert selection.round == 2


def test_second_round_carries_previous_texts_for_that_project():
    posted = [
        {"slug": "a", "round": 1, "text": "1회차 본문"},
        {"slug": "b", "round": 1, "text": "다른 프로젝트"},
    ]
    selection = choose(catalog("a"), posted, rng=rng())
    assert selection.round == 2
    assert selection.previous_texts == ("1회차 본문",)


def test_skipped_records_contribute_no_previous_text():
    posted = [{"slug": "a", "round": 1, "skipped": True}]
    selection = choose(catalog("a"), posted, rng=rng())
    assert selection.previous_texts == ()


def test_force_slug_selects_that_project_at_its_next_round():
    posted = [{"slug": "a", "round": 1, "text": "예전 글"}]
    selection = choose(catalog("a", "b"), posted, rng=rng(), force_slug="a")
    assert selection.project["slug"] == "a"
    assert selection.round == 2
    assert selection.previous_texts == ("예전 글",)


def test_force_slug_rejects_unknown_slug():
    with pytest.raises(UnknownSlugError):
        choose(catalog("a"), [], rng=rng(), force_slug="nope")


def test_empty_catalog_raises():
    with pytest.raises(NoProjectsError):
        choose({"categories": []}, [], rng=rng())


def test_selection_is_deterministic_for_a_seeded_rng():
    first = choose(catalog("a", "b", "c"), [], rng=random.Random(7))
    second = choose(catalog("a", "b", "c"), [], rng=random.Random(7))
    assert first.project["slug"] == second.project["slug"]
```

- [ ] **Step 2: 테스트가 실패하는지 확인한다**

Run: `cd scripts/threads && python3 -m pytest tests/test_selector.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'poster.selector'`

- [ ] **Step 3: 최소 구현을 쓴다**

Create `scripts/threads/poster/selector.py`:

```python
"""오늘 소개할 프로젝트를 고른다. 파일 I/O 도 네트워크도 모른다."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, Sequence


class NoProjectsError(RuntimeError):
    """projects.json 에 프로젝트가 하나도 없다."""


class UnknownSlugError(RuntimeError):
    """--project 로 지정한 slug 가 카탈로그에 없다."""


@dataclass(frozen=True)
class Selection:
    project: dict[str, Any]
    round: int
    previous_texts: tuple[str, ...]


def flatten_projects(catalog: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        project
        for category in catalog.get("categories", [])
        for project in category.get("projects", [])
    ]


def _previous_texts(posted: Sequence[dict], slug: str) -> tuple[str, ...]:
    return tuple(
        record["text"]
        for record in posted
        if record.get("slug") == slug and record.get("text")
    )


def _next_round_for(posted: Sequence[dict], slug: str) -> int:
    rounds = [r.get("round", 1) for r in posted if r.get("slug") == slug]
    return max(rounds) + 1 if rounds else 1


def choose(
    catalog: dict[str, Any],
    posted: Sequence[dict],
    *,
    rng: random.Random,
    force_slug: str | None = None,
) -> Selection:
    projects = flatten_projects(catalog)
    if not projects:
        raise NoProjectsError("projects.json 에 프로젝트가 없습니다")

    if force_slug is not None:
        project = next((p for p in projects if p.get("slug") == force_slug), None)
        if project is None:
            raise UnknownSlugError(f"알 수 없는 slug: {force_slug}")
        return Selection(
            project=project,
            round=_next_round_for(posted, force_slug),
            previous_texts=_previous_texts(posted, force_slug),
        )

    # 이번 회차에서 아직 안 다룬 프로젝트가 없으면 다음 회차를 연다.
    current = 1
    while True:
        done = {r.get("slug") for r in posted if r.get("round", 1) == current}
        candidates = [p for p in projects if p.get("slug") not in done]
        if candidates:
            break
        current += 1

    # 정렬해서 넘겨야 같은 시드로 같은 결과가 나온다.
    project = rng.choice(sorted(candidates, key=lambda p: p["slug"]))
    return Selection(
        project=project,
        round=current,
        previous_texts=_previous_texts(posted, project["slug"]),
    )
```

- [ ] **Step 4: 테스트가 통과하는지 확인한다**

Run: `cd scripts/threads && python3 -m pytest tests/test_selector.py -v`
Expected: PASS — 11 passed

- [ ] **Step 5: 실제 projects.json 으로 손검증한다**

Run:

```bash
cd scripts/threads && python3 -c "
import json, random, sys
sys.path.insert(0, '.')
from poster.selector import choose, flatten_projects
catalog = json.load(open('../../projects.json'))
print('프로젝트 수:', len(flatten_projects(catalog)))
s = choose(catalog, [], rng=random.Random(1))
print('선택:', s.project['slug'], '/ round', s.round)
"
```

Expected: `프로젝트 수: 59` 와 임의의 slug 하나

- [ ] **Step 6: 커밋한다**

```bash
git add scripts/threads/poster/selector.py scripts/threads/tests/test_selector.py
git commit -m "feat: Threads 포스터 프로젝트 선택과 회차 계산"
```

---

## Task 3: LLM 출력 정리와 길이 검증

**Files:**
- Create: `scripts/threads/poster/sanitize.py`
- Test: `scripts/threads/tests/test_sanitize.py`

- [ ] **Step 1: 실패하는 테스트를 쓴다**

Create `scripts/threads/tests/test_sanitize.py`:

```python
import pytest

from poster.sanitize import MAX_LENGTH, EmptyTextError, TooLongError, clean, validate


def test_clean_strips_surrounding_whitespace():
    assert clean("\n  본문  \n") == "본문"


def test_clean_removes_plain_code_fence():
    assert clean("```\n본문\n```") == "본문"


def test_clean_removes_language_tagged_code_fence():
    assert clean("```text\n본문\n```") == "본문"


def test_clean_removes_wrapping_straight_quotes():
    assert clean('"본문"') == "본문"


def test_clean_removes_wrapping_curly_quotes():
    assert clean("“본문”") == "본문"


def test_clean_keeps_inner_quotes():
    assert clean('그는 "안녕"이라고 했다') == '그는 "안녕"이라고 했다'


def test_clean_collapses_three_or_more_blank_lines():
    assert clean("가\n\n\n\n나") == "가\n\n나"


def test_clean_keeps_a_single_blank_line():
    assert clean("가\n\n나") == "가\n\n나"


def test_validate_returns_text_at_the_limit():
    text = "가" * MAX_LENGTH
    assert validate(text) == text


def test_validate_rejects_one_over_the_limit():
    with pytest.raises(TooLongError) as excinfo:
        validate("가" * (MAX_LENGTH + 1))
    assert excinfo.value.length == MAX_LENGTH + 1


def test_validate_rejects_empty_text():
    with pytest.raises(EmptyTextError):
        validate("")


def test_too_long_error_keeps_the_text_for_the_warning_path():
    text = "가" * (MAX_LENGTH + 5)
    with pytest.raises(TooLongError) as excinfo:
        validate(text)
    assert excinfo.value.text == text
```

- [ ] **Step 2: 테스트가 실패하는지 확인한다**

Run: `cd scripts/threads && python3 -m pytest tests/test_sanitize.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'poster.sanitize'`

- [ ] **Step 3: 최소 구현을 쓴다**

Create `scripts/threads/poster/sanitize.py`:

```python
"""LLM 이 뱉은 문자열을 게시 가능한 본문으로 정리한다."""

from __future__ import annotations

import re

MAX_LENGTH = 500  # Threads 텍스트 게시물 상한

_FENCE = re.compile(r"\A```[A-Za-z]*\n(.*)\n```\Z", re.DOTALL)
_BLANK_LINES = re.compile(r"\n{3,}")
_QUOTE_PAIRS = ('""', "''", "“”", "‘’")


class EmptyTextError(ValueError):
    """정리하고 나니 남은 내용이 없다."""


class TooLongError(ValueError):
    def __init__(self, text: str, length: int) -> None:
        super().__init__(f"{length}자 — 상한 {MAX_LENGTH}자를 넘었습니다")
        self.text = text
        self.length = length


def clean(raw: str) -> str:
    text = raw.strip()

    fence = _FENCE.match(text)
    if fence:
        text = fence.group(1).strip()

    for opening, closing in _QUOTE_PAIRS:
        if len(text) >= 2 and text.startswith(opening) and text.endswith(closing):
            text = text[1:-1].strip()
            break

    return _BLANK_LINES.sub("\n\n", text)


def validate(text: str) -> str:
    if not text:
        raise EmptyTextError("빈 문구입니다")
    if len(text) > MAX_LENGTH:
        raise TooLongError(text, len(text))
    return text
```

- [ ] **Step 4: 테스트가 통과하는지 확인한다**

Run: `cd scripts/threads && python3 -m pytest tests/test_sanitize.py -v`
Expected: PASS — 12 passed

- [ ] **Step 5: 커밋한다**

```bash
git add scripts/threads/poster/sanitize.py scripts/threads/tests/test_sanitize.py
git commit -m "feat: Threads 포스터 문구 정리와 길이 검증"
```

---

## Task 4: 설정 로딩

**Files:**
- Create: `scripts/threads/poster/config.py`
- Test: `scripts/threads/tests/test_config.py`

- [ ] **Step 1: 실패하는 테스트를 쓴다**

Create `scripts/threads/tests/test_config.py`:

```python
import pytest

from poster.config import MissingCredentialError, load_dotenv, load_telegram_credentials


def test_load_dotenv_parses_simple_pairs(tmp_path):
    env = tmp_path / ".env"
    env.write_text("A=1\nB=two\n", encoding="utf-8")
    assert load_dotenv(env) == {"A": "1", "B": "two"}


def test_load_dotenv_ignores_comments_and_blank_lines(tmp_path):
    env = tmp_path / ".env"
    env.write_text("# 주석\n\nA=1\n  # 들여쓴 주석\n", encoding="utf-8")
    assert load_dotenv(env) == {"A": "1"}


def test_load_dotenv_strips_export_prefix_and_quotes(tmp_path):
    env = tmp_path / ".env"
    env.write_text('export A="quoted"\nB=\'single\'\n', encoding="utf-8")
    assert load_dotenv(env) == {"A": "quoted", "B": "single"}


def test_load_dotenv_keeps_equals_inside_the_value(tmp_path):
    env = tmp_path / ".env"
    env.write_text("TOKEN=abc=def==\n", encoding="utf-8")
    assert load_dotenv(env) == {"TOKEN": "abc=def=="}


def test_load_dotenv_returns_empty_when_file_is_missing(tmp_path):
    assert load_dotenv(tmp_path / "nope.env") == {}


def test_load_telegram_credentials_reads_both_values(tmp_path):
    env = tmp_path / ".env"
    env.write_text(
        "TELEGRAM_BOT_TOKEN=bot-token\nAUTHORIZED_CHAT_ID=12345\n", encoding="utf-8"
    )
    assert load_telegram_credentials(env) == ("bot-token", "12345")


def test_load_telegram_credentials_raises_when_token_is_absent(tmp_path):
    env = tmp_path / ".env"
    env.write_text("AUTHORIZED_CHAT_ID=12345\n", encoding="utf-8")
    with pytest.raises(MissingCredentialError):
        load_telegram_credentials(env)


def test_load_telegram_credentials_raises_when_chat_id_is_absent(tmp_path):
    env = tmp_path / ".env"
    env.write_text("TELEGRAM_BOT_TOKEN=bot-token\n", encoding="utf-8")
    with pytest.raises(MissingCredentialError):
        load_telegram_credentials(env)
```

- [ ] **Step 2: 테스트가 실패하는지 확인한다**

Run: `cd scripts/threads && python3 -m pytest tests/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'poster.config'`

- [ ] **Step 3: 최소 구현을 쓴다**

Create `scripts/threads/poster/config.py`:

```python
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
```

- [ ] **Step 4: 테스트가 통과하는지 확인한다**

Run: `cd scripts/threads && python3 -m pytest tests/test_config.py -v`
Expected: PASS — 8 passed

- [ ] **Step 5: REPO_ROOT 가 맞는지 확인한다**

Run:

```bash
cd scripts/threads && python3 -c "
import sys; sys.path.insert(0, '.')
from poster.config import PROJECTS_JSON, PROMPT_PATH
print(PROJECTS_JSON, PROJECTS_JSON.exists())
print(PROMPT_PATH)
"
```

Expected: `/Users/zihado/work/playground/code.zihado.com/projects.json True`

- [ ] **Step 6: 커밋한다**

```bash
git add scripts/threads/poster/config.py scripts/threads/tests/test_config.py
git commit -m "feat: Threads 포스터 설정 로딩"
```

---

## Task 5: 텔레그램 연동

**Files:**
- Create: `scripts/threads/poster/telegram.py`
- Test: `scripts/threads/tests/test_telegram.py`

- [ ] **Step 1: 실패하는 테스트를 쓴다**

Create `scripts/threads/tests/test_telegram.py`:

```python
import json

import pytest

from poster.telegram import Callback, Telegram, TelegramError


class FakeTransport:
    """(method, params) 를 기록하고 미리 정한 응답을 돌려준다."""

    def __init__(self, responses=None):
        self.calls = []
        self.responses = responses or {}

    def __call__(self, method, params):
        self.calls.append((method, params))
        return self.responses.get(method, {"ok": True, "result": {}})


def make(responses=None):
    transport = FakeTransport(responses)
    return Telegram("bot-token", "12345", transport=transport), transport


def test_send_draft_returns_message_id():
    telegram, _ = make({"sendMessage": {"ok": True, "result": {"message_id": 4521}}})
    assert telegram.send_draft(slug="law", text="본문") == 4521


def test_send_draft_targets_the_authorized_chat():
    telegram, transport = make({"sendMessage": {"ok": True, "result": {"message_id": 1}}})
    telegram.send_draft(slug="law", text="본문")
    _, params = transport.calls[0]
    assert params["chat_id"] == "12345"


def test_send_draft_includes_three_buttons_with_namespaced_callback_data():
    telegram, transport = make({"sendMessage": {"ok": True, "result": {"message_id": 1}}})
    telegram.send_draft(slug="law", text="본문")
    _, params = transport.calls[0]
    row = json.loads(params["reply_markup"])["inline_keyboard"][0]
    assert [button["callback_data"] for button in row] == [
        "threads:publish:law",
        "threads:retry:law",
        "threads:skip:law",
    ]


def test_send_draft_shows_the_warning_when_given():
    telegram, transport = make({"sendMessage": {"ok": True, "result": {"message_id": 1}}})
    telegram.send_draft(slug="law", text="본문", warning="길이 초과")
    _, params = transport.calls[0]
    assert "길이 초과" in params["text"]


def test_send_draft_body_contains_the_post_text():
    telegram, transport = make({"sendMessage": {"ok": True, "result": {"message_id": 1}}})
    telegram.send_draft(slug="law", text="오늘의 본문")
    _, params = transport.calls[0]
    assert "오늘의 본문" in params["text"]


def test_notify_sends_a_plain_message():
    telegram, transport = make()
    telegram.notify("알림")
    method, params = transport.calls[0]
    assert method == "sendMessage"
    assert params["text"] == "알림"
    assert "reply_markup" not in params


def test_poll_callbacks_parses_updates_and_advances_the_offset():
    telegram, transport = make(
        {
            "getUpdates": {
                "ok": True,
                "result": [
                    {
                        "update_id": 100,
                        "callback_query": {
                            "id": "cb1",
                            "data": "threads:publish:law",
                            "message": {"message_id": 4521},
                        },
                    }
                ],
            }
        }
    )
    callbacks, offset = telegram.poll_callbacks(0)
    assert callbacks == [Callback(id="cb1", action="publish", slug="law", message_id=4521)]
    assert offset == 101


def test_poll_callbacks_passes_the_offset_through():
    telegram, transport = make({"getUpdates": {"ok": True, "result": []}})
    telegram.poll_callbacks(77)
    _, params = transport.calls[0]
    assert params["offset"] == 77


def test_poll_callbacks_keeps_the_offset_when_nothing_arrived():
    telegram, _ = make({"getUpdates": {"ok": True, "result": []}})
    callbacks, offset = telegram.poll_callbacks(77)
    assert callbacks == []
    assert offset == 77


def test_poll_callbacks_ignores_updates_from_other_features():
    telegram, _ = make(
        {
            "getUpdates": {
                "ok": True,
                "result": [
                    {"update_id": 5, "message": {"text": "안녕"}},
                    {
                        "update_id": 6,
                        "callback_query": {
                            "id": "cb",
                            "data": "other:thing:x",
                            "message": {"message_id": 9},
                        },
                    },
                ],
            }
        }
    )
    callbacks, offset = telegram.poll_callbacks(0)
    assert callbacks == []
    assert offset == 7  # 처리하지 않아도 offset 은 넘긴다


def test_resolve_edits_the_message_and_drops_the_buttons():
    telegram, transport = make()
    telegram.resolve(4521, "게시했습니다")
    method, params = transport.calls[0]
    assert method == "editMessageText"
    assert params["message_id"] == 4521
    assert params["text"] == "게시했습니다"
    assert json.loads(params["reply_markup"]) == {"inline_keyboard": []}


def test_answer_callback_acknowledges_the_button_press():
    telegram, transport = make()
    telegram.answer_callback("cb1", "처리 중")
    method, params = transport.calls[0]
    assert method == "answerCallbackQuery"
    assert params["callback_query_id"] == "cb1"


def test_api_error_is_raised_with_the_description():
    telegram, _ = make({"sendMessage": {"ok": False, "description": "chat not found"}})
    with pytest.raises(TelegramError, match="chat not found"):
        telegram.notify("알림")
```

- [ ] **Step 2: 테스트가 실패하는지 확인한다**

Run: `cd scripts/threads && python3 -m pytest tests/test_telegram.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'poster.telegram'`

- [ ] **Step 3: 최소 구현을 쓴다**

Create `scripts/threads/poster/telegram.py`:

```python
"""텔레그램 Bot API. HTTP 만 담당하고 트랜스포트는 주입받는다."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable

CALLBACK_PREFIX = "threads"
_TIMEOUT_SECONDS = 20


class TelegramError(RuntimeError):
    """텔레그램이 ok=false 를 돌려주었다."""


@dataclass(frozen=True)
class Callback:
    id: str
    action: str
    slug: str
    message_id: int


Transport = Callable[[str, dict[str, Any]], dict[str, Any]]


def _http_transport(token: str) -> Transport:
    def call(method: str, params: dict[str, Any]) -> dict[str, Any]:
        url = f"https://api.telegram.org/bot{token}/{method}"
        body = urllib.parse.urlencode(params).encode("utf-8")
        request = urllib.request.Request(url, data=body)
        with urllib.request.urlopen(request, timeout=_TIMEOUT_SECONDS) as response:
            return json.loads(response.read().decode("utf-8"))

    return call


class Telegram:
    def __init__(self, token: str, chat_id: str, *, transport: Transport | None = None):
        self._chat_id = chat_id
        self._transport = transport or _http_transport(token)

    def _call(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        payload = self._transport(method, params)
        if not payload.get("ok", False):
            raise TelegramError(payload.get("description", "알 수 없는 오류"))
        return payload

    def notify(self, text: str) -> None:
        self._call(
            "sendMessage",
            {"chat_id": self._chat_id, "text": text, "disable_web_page_preview": True},
        )

    def send_draft(self, *, slug: str, text: str, warning: str | None = None) -> int:
        header = "📝 오늘의 Threads 초안"
        if warning:
            header += f"\n⚠️ {warning}"
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "✅ 게시", "callback_data": f"{CALLBACK_PREFIX}:publish:{slug}"},
                    {"text": "🔄 다시", "callback_data": f"{CALLBACK_PREFIX}:retry:{slug}"},
                    {"text": "❌ 건너뛰기", "callback_data": f"{CALLBACK_PREFIX}:skip:{slug}"},
                ]
            ]
        }
        payload = self._call(
            "sendMessage",
            {
                "chat_id": self._chat_id,
                "text": f"{header}\n\n{text}\n\n({len(text)}자 · {slug})",
                "disable_web_page_preview": True,
                "reply_markup": json.dumps(keyboard, ensure_ascii=False),
            },
        )
        return payload["result"]["message_id"]

    def poll_callbacks(self, offset: int) -> tuple[list[Callback], int]:
        """우리 버튼만 골라 반환한다. offset 은 남의 업데이트도 지나쳐 전진한다."""
        payload = self._call(
            "getUpdates",
            {"offset": offset, "timeout": 0, "allowed_updates": json.dumps(["callback_query"])},
        )
        updates = payload.get("result", [])
        callbacks: list[Callback] = []
        next_offset = offset

        for update in updates:
            next_offset = max(next_offset, update["update_id"] + 1)
            query = update.get("callback_query")
            if not query:
                continue
            parts = str(query.get("data", "")).split(":")
            if len(parts) != 3 or parts[0] != CALLBACK_PREFIX:
                continue
            callbacks.append(
                Callback(
                    id=query["id"],
                    action=parts[1],
                    slug=parts[2],
                    message_id=query["message"]["message_id"],
                )
            )

        return callbacks, next_offset

    def resolve(self, message_id: int, text: str) -> None:
        self._call(
            "editMessageText",
            {
                "chat_id": self._chat_id,
                "message_id": message_id,
                "text": text,
                "disable_web_page_preview": True,
                "reply_markup": json.dumps({"inline_keyboard": []}),
            },
        )

    def answer_callback(self, callback_id: str, text: str) -> None:
        self._call("answerCallbackQuery", {"callback_query_id": callback_id, "text": text})
```

- [ ] **Step 4: 테스트가 통과하는지 확인한다**

Run: `cd scripts/threads && python3 -m pytest tests/test_telegram.py -v`
Expected: PASS — 13 passed

- [ ] **Step 5: 커밋한다**

```bash
git add scripts/threads/poster/telegram.py scripts/threads/tests/test_telegram.py
git commit -m "feat: Threads 포스터 텔레그램 연동"
```

---

## Task 6: Threads API 클라이언트

**Files:**
- Create: `scripts/threads/poster/threads_api.py`
- Test: `scripts/threads/tests/test_threads_api.py`

- [ ] **Step 1: 실패하는 테스트를 쓴다**

Create `scripts/threads/tests/test_threads_api.py`:

```python
from datetime import datetime, timedelta, timezone

import pytest

from poster.threads_api import (
    REFRESH_AFTER_DAYS,
    ThreadsClient,
    ThreadsError,
    needs_refresh,
)


class FakeTransport:
    def __init__(self, responses):
        self.calls = []
        self._responses = list(responses)

    def __call__(self, method, url, params):
        self.calls.append((method, url, params))
        result = self._responses.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


def make(responses):
    transport = FakeTransport(responses)
    slept = []
    client = ThreadsClient(
        "user-1", "token-1", transport=transport, sleep=slept.append
    )
    return client, transport, slept


def test_create_container_returns_the_creation_id():
    client, _, _ = make([{"id": "container-9"}])
    assert client.create_container("본문") == "container-9"


def test_create_container_sends_text_media_type_and_the_body():
    client, transport, _ = make([{"id": "c"}])
    client.create_container("본문")
    method, url, params = transport.calls[0]
    assert method == "POST"
    assert url.endswith("/user-1/threads")
    assert params["media_type"] == "TEXT"
    assert params["text"] == "본문"
    assert params["access_token"] == "token-1"


def test_publish_returns_the_thread_id():
    client, _, _ = make([{"id": "thread-7"}])
    assert client.publish("container-9") == "thread-7"


def test_publish_waits_before_calling_the_api():
    client, _, slept = make([{"id": "thread-7"}])
    client.publish("container-9")
    assert slept == [client.publish_delay_seconds]


def test_publish_sends_the_creation_id():
    client, transport, _ = make([{"id": "t"}])
    client.publish("container-9")
    _, url, params = transport.calls[0]
    assert url.endswith("/user-1/threads_publish")
    assert params["creation_id"] == "container-9"


def test_api_error_payload_is_raised():
    client, _, _ = make([{"error": {"message": "Invalid OAuth access token"}}])
    with pytest.raises(ThreadsError, match="Invalid OAuth access token"):
        client.create_container("본문")


def test_missing_id_in_response_is_an_error():
    client, _, _ = make([{}])
    with pytest.raises(ThreadsError):
        client.create_container("본문")


def test_refresh_token_returns_the_new_token():
    client, transport, _ = make([{"access_token": "token-2", "expires_in": 5184000}])
    assert client.refresh_token() == "token-2"
    method, url, params = transport.calls[0]
    assert method == "GET"
    assert url.endswith("/refresh_access_token")
    assert params["grant_type"] == "th_refresh_token"


def test_needs_refresh_is_false_for_a_fresh_token():
    now = datetime(2026, 8, 9, tzinfo=timezone.utc)
    recent = (now - timedelta(days=REFRESH_AFTER_DAYS - 1)).isoformat()
    assert needs_refresh(recent, now) is False


def test_needs_refresh_is_true_past_the_threshold():
    now = datetime(2026, 8, 9, tzinfo=timezone.utc)
    old = (now - timedelta(days=REFRESH_AFTER_DAYS + 1)).isoformat()
    assert needs_refresh(old, now) is True


def test_needs_refresh_is_true_when_the_timestamp_is_missing():
    assert needs_refresh(None, datetime(2026, 8, 9, tzinfo=timezone.utc)) is True


def test_needs_refresh_is_true_when_the_timestamp_is_unparseable():
    assert needs_refresh("어제", datetime(2026, 8, 9, tzinfo=timezone.utc)) is True
```

- [ ] **Step 2: 테스트가 실패하는지 확인한다**

Run: `cd scripts/threads && python3 -m pytest tests/test_threads_api.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'poster.threads_api'`

- [ ] **Step 3: 최소 구현을 쓴다**

Create `scripts/threads/poster/threads_api.py`:

```python
"""Threads Graph API. HTTP 만 담당하고 트랜스포트는 주입받는다."""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from typing import Any, Callable

API_ROOT = "https://graph.threads.net/v1.0"
REFRESH_AFTER_DAYS = 30  # 수명 60일. 절반쯤에서 갱신해 여유를 남긴다.
PUBLISH_DELAY_SECONDS = 30  # 컨테이너 생성 후 권장 대기
_TIMEOUT_SECONDS = 30


class ThreadsError(RuntimeError):
    """Threads API 가 오류를 돌려주었거나 예상한 필드가 없다."""


Transport = Callable[[str, str, dict[str, Any]], dict[str, Any]]


def _http_transport() -> Transport:
    def call(method: str, url: str, params: dict[str, Any]) -> dict[str, Any]:
        encoded = urllib.parse.urlencode(params)
        if method == "GET":
            request = urllib.request.Request(f"{url}?{encoded}", method="GET")
        else:
            request = urllib.request.Request(url, data=encoded.encode("utf-8"), method="POST")
        with urllib.request.urlopen(request, timeout=_TIMEOUT_SECONDS) as response:
            return json.loads(response.read().decode("utf-8"))

    return call


def needs_refresh(refreshed_at: str | None, now: datetime) -> bool:
    """모르면 갱신한다. 만료된 토큰으로 조용히 실패하는 것보다 낫다."""
    if not refreshed_at:
        return True
    try:
        stamp = datetime.fromisoformat(refreshed_at)
    except ValueError:
        return True
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=now.tzinfo)
    return now - stamp >= timedelta(days=REFRESH_AFTER_DAYS)


class ThreadsClient:
    publish_delay_seconds = PUBLISH_DELAY_SECONDS

    def __init__(
        self,
        user_id: str,
        token: str,
        *,
        transport: Transport | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._user_id = user_id
        self._token = token
        self._transport = transport or _http_transport()
        self._sleep = sleep

    def _call(self, method: str, url: str, params: dict[str, Any]) -> dict[str, Any]:
        payload = self._transport(method, url, params)
        if "error" in payload:
            raise ThreadsError(payload["error"].get("message", "알 수 없는 오류"))
        return payload

    def create_container(self, text: str) -> str:
        payload = self._call(
            "POST",
            f"{API_ROOT}/{self._user_id}/threads",
            {"media_type": "TEXT", "text": text, "access_token": self._token},
        )
        creation_id = payload.get("id")
        if not creation_id:
            raise ThreadsError(f"컨테이너 응답에 id 가 없습니다: {payload}")
        return creation_id

    def publish(self, creation_id: str) -> str:
        self._sleep(self.publish_delay_seconds)
        payload = self._call(
            "POST",
            f"{API_ROOT}/{self._user_id}/threads_publish",
            {"creation_id": creation_id, "access_token": self._token},
        )
        thread_id = payload.get("id")
        if not thread_id:
            raise ThreadsError(f"게시 응답에 id 가 없습니다: {payload}")
        return thread_id

    def refresh_token(self) -> str:
        payload = self._call(
            "GET",
            f"{API_ROOT}/refresh_access_token",
            {"grant_type": "th_refresh_token", "access_token": self._token},
        )
        token = payload.get("access_token")
        if not token:
            raise ThreadsError(f"갱신 응답에 access_token 이 없습니다: {payload}")
        return token
```

- [ ] **Step 4: 테스트가 통과하는지 확인한다**

Run: `cd scripts/threads && python3 -m pytest tests/test_threads_api.py -v`
Expected: PASS — 12 passed

- [ ] **Step 5: 커밋한다**

```bash
git add scripts/threads/poster/threads_api.py scripts/threads/tests/test_threads_api.py
git commit -m "feat: Threads API 클라이언트와 토큰 갱신"
```

---

## Task 7: 문구 작성 지침

**Files:**
- Create: `scripts/threads/compose-prompt.md`

이 태스크에는 테스트가 없다. 산출물이 프롬프트 텍스트이기 때문이다.
Task 8에서 이 파일을 읽어 조립하는 코드를 테스트한다.

- [ ] **Step 1: 지침 파일을 만든다**

Create `scripts/threads/compose-prompt.md`:

```markdown
당신은 "100개 서비스 만들기 프로젝트"를 진행 중인 개발자의 Threads 포스팅을 대신 씁니다.
아래 프로젝트 하나를 소개하는 한국어 포스팅 본문을 작성하세요.

## 출력 형식 (엄수)

- **본문 텍스트만** 출력합니다. 설명, 머리말, 맺음말, 마크다운 코드 펜스를 붙이지 마세요.
- **500자를 절대 넘지 마세요.** 공백과 이모지를 포함한 글자 수입니다. 400자 안팎이 적당합니다.
- 문단은 2~4개, 각 문단은 1~3문장으로 짧게 끊습니다. 모바일 피드에서 읽힙니다.

## 톤

- 성과 자랑이 아니라 **"이런 걸 만들어봤고, 만들면서 이런 걸 배웠다"** 입니다.
- 읽는 사람은 개발을 막 시작했거나 관심만 있는 동네 주민입니다. 전문 용어를 쓸 때는
  한 마디로 풀어주세요. ("전문검색 엔진 — 수십만 건에서 원하는 문장을 즉시 찾아주는 도구")
- 겸손하되 위축되지 않게. 과장된 수식어("혁신적인", "완벽한")는 쓰지 마세요.
- 이모지는 전체에서 2개 이하로 아껴 씁니다.

## 구성

1. 무엇을 만들었는지 (`name`, `oneLiner`, `does` 참고)
2. 만들면서 배운 것 또는 막혔던 지점 — **여기가 핵심입니다** (`learn` 참고)
3. `live` 값이 있으면 마지막에 URL만 한 줄로. 없으면 링크 없이 마무리합니다.
4. 해시태그 한 줄: `#100개서비스만들기` 를 반드시 포함하고, 프로젝트 성격에 맞는 것
   1~2개를 더합니다.

## 쓰지 말 것

- `stack`을 나열하지 마세요. 기술 이름은 이야기에 필요한 것만 1~2개 자연스럽게 녹입니다.
- `folder`, `slug`, `status`, `started`, `updated` 값은 본문에 등장시키지 마세요.
- "여러분도 만들어보세요" 같은 상투적 권유로 끝내지 마세요.
```

- [ ] **Step 2: 파일이 읽히는지 확인한다**

Run: `wc -c scripts/threads/compose-prompt.md`
Expected: 1000자 이상 출력

- [ ] **Step 3: 커밋한다**

```bash
git add scripts/threads/compose-prompt.md
git commit -m "feat: Threads 문구 작성 지침"
```

---

## Task 8: 프롬프트 조립과 claude 호출

**Files:**
- Create: `scripts/threads/poster/composer.py`
- Test: `scripts/threads/tests/test_composer.py`

- [ ] **Step 1: 실패하는 테스트를 쓴다**

Create `scripts/threads/tests/test_composer.py`:

```python
import pytest

from poster.composer import ComposeFailed, ComposeResult, build_prompt, compose
from poster.selector import Selection


def selection(round_=1, previous=()):
    return Selection(
        project={"slug": "law", "name": "법령 검색", "live": "https://law.zihado.com"},
        round=round_,
        previous_texts=previous,
    )


def test_build_prompt_starts_with_the_instructions():
    prompt = build_prompt("지침 본문", selection())
    assert prompt.startswith("지침 본문")


def test_build_prompt_embeds_the_project_json():
    prompt = build_prompt("지침", selection())
    assert '"slug": "law"' in prompt
    assert "법령 검색" in prompt


def test_build_prompt_omits_previous_texts_on_the_first_round():
    prompt = build_prompt("지침", selection())
    assert "이전 회차" not in prompt


def test_build_prompt_includes_previous_texts_from_the_second_round():
    prompt = build_prompt("지침", selection(round_=2, previous=("예전에 쓴 글",)))
    assert "이전 회차" in prompt
    assert "예전에 쓴 글" in prompt


def test_compose_returns_the_cleaned_text():
    result = compose("지침", selection(), runner=lambda prompt: "```\n  본문  \n```")
    assert result == ComposeResult(text="본문", warning=None)


def test_compose_retries_once_when_the_first_draft_is_too_long():
    drafts = iter(["가" * 600, "짧은 본문"])
    calls = []

    def runner(prompt):
        calls.append(prompt)
        return next(drafts)

    result = compose("지침", selection(), runner=runner)
    assert result.text == "짧은 본문"
    assert result.warning is None
    assert len(calls) == 2


def test_the_retry_prompt_tells_the_model_it_was_too_long():
    drafts = iter(["가" * 600, "짧은 본문"])
    calls = []

    def runner(prompt):
        calls.append(prompt)
        return next(drafts)

    compose("지침", selection(), runner=runner)
    assert "500자" in calls[1]


def test_compose_surrenders_with_a_warning_after_two_long_drafts():
    result = compose("지침", selection(), runner=lambda prompt: "가" * 600)
    assert result.text == "가" * 600
    assert result.warning is not None
    assert "600" in result.warning


def test_compose_raises_when_the_model_returns_nothing():
    with pytest.raises(ComposeFailed):
        compose("지침", selection(), runner=lambda prompt: "   ")


def test_compose_raises_when_the_runner_blows_up():
    def runner(prompt):
        raise OSError("claude 를 찾을 수 없습니다")

    with pytest.raises(ComposeFailed, match="claude"):
        compose("지침", selection(), runner=runner)
```

- [ ] **Step 2: 테스트가 실패하는지 확인한다**

Run: `cd scripts/threads && python3 -m pytest tests/test_composer.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'poster.composer'`

- [ ] **Step 3: 최소 구현을 쓴다**

Create `scripts/threads/poster/composer.py`:

```python
"""프롬프트를 조립하고 headless claude 를 호출한다."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from poster.sanitize import MAX_LENGTH, EmptyTextError, TooLongError, clean, validate
from poster.selector import Selection

_MODEL = "claude-sonnet-5"
_MAX_TURNS = "3"
_TIMEOUT_SECONDS = 300


class ComposeFailed(RuntimeError):
    """문구를 만들지 못했다."""


@dataclass(frozen=True)
class ComposeResult:
    text: str
    warning: str | None


Runner = Callable[[str], str]


def claude_runner(claude_path: Path | str) -> Runner:
    def run(prompt: str) -> str:
        completed = subprocess.run(
            [str(claude_path), "-p", prompt, "--model", _MODEL, "--max-turns", _MAX_TURNS],
            capture_output=True,
            text=True,
            timeout=_TIMEOUT_SECONDS,
        )
        if completed.returncode != 0:
            raise OSError(f"claude 실패 (exit {completed.returncode}): {completed.stderr.strip()}")
        return completed.stdout

    return run


def build_prompt(instructions: str, selection: Selection, *, retry_hint: bool = False) -> str:
    blocks = [
        instructions,
        "## 오늘 소개할 프로젝트\n\n```json\n"
        + json.dumps(selection.project, ensure_ascii=False, indent=2)
        + "\n```",
    ]

    if selection.previous_texts:
        earlier = "\n\n---\n\n".join(selection.previous_texts)
        blocks.append(
            "## 이전 회차에 쓴 글\n\n"
            "같은 프로젝트를 다시 소개합니다. 아래와 **다른 각도**로 쓰세요.\n\n"
            f"{earlier}"
        )

    if retry_hint:
        blocks.append(
            f"## 다시 씁니다\n\n직전 초안이 {MAX_LENGTH}자를 넘었습니다. "
            f"내용을 덜어내고 {MAX_LENGTH}자 안에 확실히 들어오게 쓰세요."
        )

    return "\n\n".join(blocks)


def compose(instructions: str, selection: Selection, *, runner: Runner) -> ComposeResult:
    """길이 초과면 한 번 다시 쓴다. 두 번째도 길면 경고를 달아 사람에게 넘긴다."""
    last_too_long: TooLongError | None = None

    for attempt in range(2):
        prompt = build_prompt(instructions, selection, retry_hint=attempt > 0)
        try:
            raw = runner(prompt)
        except Exception as exc:  # noqa: BLE001 — 원인을 텔레그램에 그대로 싣는다
            raise ComposeFailed(f"문구 생성 실패: {exc}") from exc

        text = clean(raw)
        try:
            return ComposeResult(text=validate(text), warning=None)
        except EmptyTextError as exc:
            raise ComposeFailed("모델이 빈 문구를 돌려주었습니다") from exc
        except TooLongError as exc:
            last_too_long = exc

    assert last_too_long is not None
    return ComposeResult(
        text=last_too_long.text,
        warning=f"길이 초과 ({last_too_long.length}자) — 직접 줄여야 합니다",
    )
```

- [ ] **Step 4: 테스트가 통과하는지 확인한다**

Run: `cd scripts/threads && python3 -m pytest tests/test_composer.py -v`
Expected: PASS — 10 passed

- [ ] **Step 5: 커밋한다**

```bash
git add scripts/threads/poster/composer.py scripts/threads/tests/test_composer.py
git commit -m "feat: Threads 문구 프롬프트 조립과 claude 호출"
```

---

## Task 9: 초안 생성 진입점

**Files:**
- Create: `scripts/threads/compose.py`
- Test: `scripts/threads/tests/test_compose_entry.py`

- [ ] **Step 1: 실패하는 테스트를 쓴다**

Create `scripts/threads/tests/test_compose_entry.py`:

```python
import json

import pytest

from compose import run
from poster.state import State


class FakeTelegram:
    def __init__(self):
        self.drafts = []
        self.notices = []

    def send_draft(self, *, slug, text, warning=None):
        self.drafts.append({"slug": slug, "text": text, "warning": warning})
        return 4521

    def notify(self, text):
        self.notices.append(text)


def catalog_file(tmp_path, *slugs):
    path = tmp_path / "projects.json"
    path.write_text(
        json.dumps(
            {"categories": [{"id": "web", "projects": [{"slug": s} for s in slugs]}]},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return path


def prompt_file(tmp_path):
    path = tmp_path / "compose-prompt.md"
    path.write_text("지침", encoding="utf-8")
    return path


def call(tmp_path, *, runner=lambda p: "본문", telegram=None, force_slug=None, dry_run=False):
    telegram = telegram or FakeTelegram()
    state = State(tmp_path / "state")
    exit_code = run(
        state=state,
        telegram=telegram,
        catalog_path=catalog_file(tmp_path, "a", "b"),
        prompt_path=prompt_file(tmp_path),
        runner=runner,
        force_slug=force_slug,
        dry_run=dry_run,
        seed=1,
    )
    return exit_code, telegram, state


def test_sends_a_draft_and_records_pending(tmp_path):
    exit_code, telegram, state = call(tmp_path)
    assert exit_code == 0
    assert len(telegram.drafts) == 1
    pending = state.read_json("pending.json", None)
    assert pending["text"] == "본문"
    assert pending["telegramMessageId"] == 4521
    assert pending["creationId"] is None


def test_pending_records_the_selected_round(tmp_path):
    _, _, state = call(tmp_path)
    assert state.read_json("pending.json", None)["round"] == 1


def test_does_not_stack_drafts_when_one_is_already_pending(tmp_path):
    _, _, state = call(tmp_path)
    telegram = FakeTelegram()
    exit_code = run(
        state=state,
        telegram=telegram,
        catalog_path=catalog_file(tmp_path, "a", "b"),
        prompt_path=prompt_file(tmp_path),
        runner=lambda p: "새 본문",
        force_slug=None,
        dry_run=False,
        seed=1,
    )
    assert exit_code == 0
    assert telegram.drafts == []
    assert "대기" in telegram.notices[0]


def test_dry_run_sends_nothing_and_writes_no_pending(tmp_path):
    exit_code, telegram, state = call(tmp_path, dry_run=True)
    assert exit_code == 0
    assert telegram.drafts == []
    assert state.read_json("pending.json", None) is None


def test_force_slug_overrides_the_random_pick(tmp_path):
    _, _, state = call(tmp_path, force_slug="b")
    assert state.read_json("pending.json", None)["slug"] == "b"


def test_warning_from_a_too_long_draft_reaches_telegram(tmp_path):
    _, telegram, _ = call(tmp_path, runner=lambda p: "가" * 600)
    assert telegram.drafts[0]["warning"] is not None


def test_compose_failure_notifies_and_exits_nonzero(tmp_path):
    def runner(prompt):
        raise OSError("claude 없음")

    exit_code, telegram, state = call(tmp_path, runner=runner)
    assert exit_code == 1
    assert any("claude 없음" in notice for notice in telegram.notices)
    assert state.read_json("pending.json", None) is None


def test_broken_catalog_notifies_and_exits_nonzero(tmp_path):
    broken = tmp_path / "projects.json"
    broken.write_text("{ this is not json", encoding="utf-8")
    telegram = FakeTelegram()
    exit_code = run(
        state=State(tmp_path / "state"),
        telegram=telegram,
        catalog_path=broken,
        prompt_path=prompt_file(tmp_path),
        runner=lambda p: "본문",
        force_slug=None,
        dry_run=False,
        seed=1,
    )
    assert exit_code == 1
    assert telegram.notices
```

- [ ] **Step 2: 테스트가 실패하는지 확인한다**

Run: `cd scripts/threads && python3 -m pytest tests/test_compose_entry.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'compose'`

- [ ] **Step 3: 최소 구현을 쓴다**

Create `scripts/threads/compose.py`:

```python
#!/usr/bin/env python3
"""매일 08:00 — 오늘 소개할 프로젝트를 골라 초안을 만들고 텔레그램으로 보낸다."""

from __future__ import annotations

import argparse
import json
import logging
import random
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from poster import config
from poster.composer import ComposeFailed, claude_runner, compose
from poster.selector import choose
from poster.state import LockBusy, State, exclusive_lock
from poster.telegram import Telegram

log = logging.getLogger("threads.compose")


def run(
    *,
    state,
    telegram,
    catalog_path: Path,
    prompt_path: Path,
    runner,
    force_slug: str | None,
    dry_run: bool,
    seed: int | None = None,
) -> int:
    if state.read_json("pending.json", None) is not None:
        telegram.notify("🟡 어제 초안이 아직 승인 대기 중입니다. 오늘 초안은 만들지 않았어요.")
        return 0

    try:
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        instructions = prompt_path.read_text(encoding="utf-8")
    except (OSError, json.JSONDecodeError) as exc:
        telegram.notify(f"🔴 Threads 초안 실패 — 입력 파일을 읽지 못했습니다: {exc}")
        return 1

    try:
        selection = choose(
            catalog,
            state.read_json("posted.json", []),
            rng=random.Random(seed),
            force_slug=force_slug,
        )
    except Exception as exc:  # noqa: BLE001
        telegram.notify(f"🔴 Threads 초안 실패 — 프로젝트를 고르지 못했습니다: {exc}")
        return 1

    try:
        result = compose(instructions, selection, runner=runner)
    except ComposeFailed as exc:
        telegram.notify(f"🔴 Threads 초안 실패 — {exc}")
        return 1

    if dry_run:
        print(f"--- {selection.project['slug']} / round {selection.round} ---")
        print(result.text)
        print(f"--- {len(result.text)}자 / warning={result.warning} ---")
        return 0

    message_id = telegram.send_draft(
        slug=selection.project["slug"], text=result.text, warning=result.warning
    )
    state.write_json(
        "pending.json",
        {
            "slug": selection.project["slug"],
            "round": selection.round,
            "text": result.text,
            "createdAt": datetime.now().astimezone().isoformat(),
            "telegramMessageId": message_id,
            "creationId": None,
        },
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Threads 초안 생성")
    parser.add_argument("--project", dest="force_slug", help="특정 slug 를 강제 지정")
    parser.add_argument("--dry-run", action="store_true", help="전송하지 않고 출력만")
    args = parser.parse_args(argv)

    config.LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=config.LOG_PATH,
        level=logging.INFO,
        format="%(asctime)s compose %(levelname)s %(message)s",
    )

    token, chat_id = config.load_telegram_credentials()
    telegram = Telegram(token, chat_id)

    try:
        with exclusive_lock(config.STATE_DIR):
            return run(
                state=State(config.STATE_DIR),
                telegram=telegram,
                catalog_path=config.PROJECTS_JSON,
                prompt_path=config.PROMPT_PATH,
                runner=claude_runner(config.CLAUDE_PATH),
                force_slug=args.force_slug,
                dry_run=args.dry_run,
            )
    except LockBusy:
        log.info("다른 인스턴스가 실행 중 — 건너뜁니다")
        return 0
    except Exception as exc:  # noqa: BLE001 — 조용히 죽지 않는다
        log.exception("compose 실패")
        telegram.notify(f"🔴 Threads 초안 실패 — {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: 테스트가 통과하는지 확인한다**

Run: `cd scripts/threads && python3 -m pytest tests/test_compose_entry.py -v`
Expected: PASS — 8 passed

- [ ] **Step 5: 실행 권한을 준다**

```bash
chmod +x scripts/threads/compose.py
```

- [ ] **Step 6: 커밋한다**

```bash
git add scripts/threads/compose.py scripts/threads/tests/test_compose_entry.py
git commit -m "feat: Threads 초안 생성 진입점"
```

---

## Task 10: 승인 폴링 진입점

이 태스크의 테스트는 **중복 게시가 일어나지 않는지**에 집중한다. 이 시스템에서 가장
위험한 실패 모드다.

**Files:**
- Create: `scripts/threads/approve.py`
- Test: `scripts/threads/tests/test_approve_entry.py`

- [ ] **Step 1: 실패하는 테스트를 쓴다**

Create `scripts/threads/tests/test_approve_entry.py`:

```python
import pytest

from approve import run
from poster.state import State
from poster.telegram import Callback
from poster.threads_api import ThreadsError


class FakeTelegram:
    def __init__(self, callbacks=None):
        self._callbacks = list(callbacks or [])
        self.notices = []
        self.resolved = []
        self.answered = []

    def poll_callbacks(self, offset):
        callbacks, self._callbacks = self._callbacks, []
        return callbacks, offset + len(callbacks)

    def notify(self, text):
        self.notices.append(text)

    def resolve(self, message_id, text):
        self.resolved.append((message_id, text))

    def answer_callback(self, callback_id, text):
        self.answered.append(callback_id)


class FakeThreads:
    def __init__(self, *, create_fails=False, publish_fails=False):
        self.created = []
        self.published = []
        self._create_fails = create_fails
        self._publish_fails = publish_fails

    def create_container(self, text):
        if self._create_fails:
            raise ThreadsError("컨테이너 생성 실패")
        self.created.append(text)
        return "container-1"

    def publish(self, creation_id):
        if self._publish_fails:
            raise ThreadsError("게시 실패")
        self.published.append(creation_id)
        return "thread-1"


def pending(state, **overrides):
    record = {
        "slug": "law",
        "round": 1,
        "text": "본문",
        "createdAt": "2026-08-09T08:00:00+09:00",
        "telegramMessageId": 4521,
        "creationId": None,
    }
    record.update(overrides)
    state.write_json("pending.json", record)


def approve_callback():
    return Callback(id="cb1", action="publish", slug="law", message_id=4521)


def call(tmp_path, *, callbacks=(), threads=None, state=None, recompose=None):
    state = state or State(tmp_path / "state")
    telegram = FakeTelegram(callbacks)
    threads = threads or FakeThreads()
    exit_code = run(
        state=state,
        telegram=telegram,
        threads=threads,
        recompose=recompose or (lambda: None),
    )
    return exit_code, state, telegram, threads


def test_does_nothing_when_no_draft_is_pending(tmp_path):
    exit_code, _, telegram, threads = call(tmp_path, callbacks=[approve_callback()])
    assert exit_code == 0
    assert threads.published == []
    assert telegram.notices == []


def test_publish_callback_posts_and_records_the_thread(tmp_path):
    state = State(tmp_path / "state")
    pending(state)
    _, state, telegram, threads = call(
        tmp_path, callbacks=[approve_callback()], state=state
    )
    assert threads.published == ["container-1"]
    posted = state.read_json("posted.json", [])
    assert posted[0]["slug"] == "law"
    assert posted[0]["threadId"] == "thread-1"
    assert posted[0]["text"] == "본문"
    assert state.read_json("pending.json", None) is None


def test_skip_callback_records_a_skip_without_posting(tmp_path):
    state = State(tmp_path / "state")
    pending(state)
    callback = Callback(id="cb", action="skip", slug="law", message_id=4521)
    _, state, _, threads = call(tmp_path, callbacks=[callback], state=state)
    assert threads.created == []
    posted = state.read_json("posted.json", [])
    assert posted[0]["skipped"] is True
    assert state.read_json("pending.json", None) is None


def test_retry_callback_clears_pending_and_recomposes(tmp_path):
    state = State(tmp_path / "state")
    pending(state)
    calls = []
    callback = Callback(id="cb", action="retry", slug="law", message_id=4521)
    call(tmp_path, callbacks=[callback], state=state, recompose=lambda: calls.append(1))
    assert calls == [1]


def test_callback_for_a_different_project_is_ignored(tmp_path):
    state = State(tmp_path / "state")
    pending(state)
    stale = Callback(id="cb", action="publish", slug="asm", message_id=99)
    _, state, _, threads = call(tmp_path, callbacks=[stale], state=state)
    assert threads.published == []
    assert state.read_json("pending.json", None) is not None


def test_offset_is_persisted_so_the_same_update_is_not_replayed(tmp_path):
    state = State(tmp_path / "state")
    pending(state)
    call(tmp_path, callbacks=[approve_callback()], state=state)
    assert state.read_json("offset.json", {"offset": 0})["offset"] == 1


def test_publish_failure_keeps_the_creation_id_for_a_retry(tmp_path):
    state = State(tmp_path / "state")
    pending(state)
    call(
        tmp_path,
        callbacks=[approve_callback()],
        state=state,
        threads=FakeThreads(publish_fails=True),
    )
    still_pending = state.read_json("pending.json", None)
    assert still_pending is not None
    assert still_pending["creationId"] == "container-1"


def test_retrying_a_failed_publish_does_not_create_a_second_container(tmp_path):
    state = State(tmp_path / "state")
    pending(state, creationId="container-1")
    _, state, _, threads = call(tmp_path, state=state)  # 콜백 없이 재시도
    assert threads.created == []
    assert threads.published == ["container-1"]
    assert state.read_json("pending.json", None) is None


def test_container_failure_leaves_pending_intact_for_the_next_run(tmp_path):
    state = State(tmp_path / "state")
    pending(state)
    _, state, telegram, _ = call(
        tmp_path,
        callbacks=[approve_callback()],
        state=state,
        threads=FakeThreads(create_fails=True),
    )
    assert state.read_json("pending.json", None) is not None
    assert any("컨테이너 생성 실패" in notice for notice in telegram.notices)


def test_the_approval_button_is_acknowledged(tmp_path):
    state = State(tmp_path / "state")
    pending(state)
    _, _, telegram, _ = call(tmp_path, callbacks=[approve_callback()], state=state)
    assert telegram.answered == ["cb1"]


def test_the_draft_message_is_edited_after_publishing(tmp_path):
    state = State(tmp_path / "state")
    pending(state)
    _, _, telegram, _ = call(tmp_path, callbacks=[approve_callback()], state=state)
    assert telegram.resolved[0][0] == 4521
```

- [ ] **Step 2: 테스트가 실패하는지 확인한다**

Run: `cd scripts/threads && python3 -m pytest tests/test_approve_entry.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'approve'`

- [ ] **Step 3: 최소 구현을 쓴다**

Create `scripts/threads/approve.py`:

```python
#!/usr/bin/env python3
"""5분마다 — 텔레그램 버튼 응답을 확인해 게시하거나 건너뛴다."""

from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from compose import run as compose_run
from poster import config
from poster.composer import claude_runner
from poster.state import LockBusy, State, exclusive_lock
from poster.telegram import Telegram
from poster.threads_api import ThreadsClient, ThreadsError, needs_refresh

log = logging.getLogger("threads.approve")


def _finish_publish(state, telegram, threads, pending) -> None:
    """컨테이너를 만들고 게시한다. creationId 가 이미 있으면 게시만 재시도한다."""
    creation_id = pending.get("creationId")
    if not creation_id:
        creation_id = threads.create_container(pending["text"])
        # 게시 전에 저장한다. 여기서 죽어도 컨테이너를 두 번 만들지 않는다.
        state.write_json("pending.json", {**pending, "creationId": creation_id})

    thread_id = threads.publish(creation_id)

    posted = state.read_json("posted.json", [])
    posted.append(
        {
            "slug": pending["slug"],
            "round": pending["round"],
            "postedAt": datetime.now().astimezone().isoformat(),
            "threadId": thread_id,
            "text": pending["text"],
        }
    )
    state.write_json("posted.json", posted)
    state.delete("pending.json")

    telegram.resolve(pending["telegramMessageId"], f"✅ 게시했습니다 — {pending['slug']}")


def _record_skip(state, telegram, pending) -> None:
    posted = state.read_json("posted.json", [])
    posted.append(
        {
            "slug": pending["slug"],
            "round": pending["round"],
            "postedAt": datetime.now().astimezone().isoformat(),
            "skipped": True,
        }
    )
    state.write_json("posted.json", posted)
    state.delete("pending.json")
    telegram.resolve(pending["telegramMessageId"], f"❌ 건너뛰었습니다 — {pending['slug']}")


def run(*, state, telegram, threads, recompose) -> int:
    pending = state.read_json("pending.json", None)
    if pending is None:
        return 0

    # 지난번에 컨테이너까지 만들고 실패한 건이면 승인을 기다리지 않고 게시를 마저 끝낸다.
    if pending.get("creationId"):
        try:
            _finish_publish(state, telegram, threads, pending)
        except ThreadsError as exc:
            telegram.notify(f"🔴 Threads 게시 재시도 실패 — {exc}")
            return 1
        return 0

    offset = state.read_json("offset.json", {"offset": 0})["offset"]
    callbacks, next_offset = telegram.poll_callbacks(offset)
    # 행동하기 전에 offset 을 먼저 저장한다. 중간에 죽어도 같은 버튼을 두 번 처리하지 않는다.
    state.write_json("offset.json", {"offset": next_offset})

    for callback in callbacks:
        if callback.slug != pending["slug"]:
            continue  # 지난 초안의 버튼

        telegram.answer_callback(callback.id, "처리 중…")

        if callback.action == "publish":
            try:
                _finish_publish(state, telegram, threads, pending)
            except ThreadsError as exc:
                telegram.notify(f"🔴 Threads 게시 실패 — {exc}\n다음 폴링에서 다시 시도합니다.")
                return 1
            return 0

        if callback.action == "skip":
            _record_skip(state, telegram, pending)
            return 0

        if callback.action == "retry":
            state.delete("pending.json")
            telegram.resolve(pending["telegramMessageId"], f"🔄 다시 씁니다 — {pending['slug']}")
            recompose()
            return 0

    return 0


def _recompose(state, telegram, slug: str):
    """compose 를 같은 프로세스 안에서 부른다.

    하위 프로세스로 compose.py 를 띄우면 이 함수가 쥐고 있는 잠금을
    compose.py 가 다시 잡으려다 LockBusy 로 조용히 죽는다. 새 초안이 영영 오지 않는다.
    """

    def call() -> None:
        compose_run(
            state=state,
            telegram=telegram,
            catalog_path=config.PROJECTS_JSON,
            prompt_path=config.PROMPT_PATH,
            runner=claude_runner(config.CLAUDE_PATH),
            force_slug=slug,
            dry_run=False,
        )

    return call


def _load_client(state, telegram) -> ThreadsClient:
    token_record = state.read_json("token.json", None)
    if token_record is None:
        raise RuntimeError(
            "token.json 이 없습니다. scripts/threads/README.md 의 토큰 발급 절차를 보세요."
        )

    client = ThreadsClient(token_record["userId"], token_record["token"])
    if needs_refresh(token_record.get("refreshedAt"), datetime.now(timezone.utc)):
        try:
            new_token = client.refresh_token()
        except ThreadsError as exc:
            telegram.notify(
                f"🔴 Threads 토큰 갱신 실패 — {exc}\n"
                "수동 재발급이 필요합니다: scripts/threads/README.md"
            )
            return client
        state.write_json(
            "token.json",
            {
                "userId": token_record["userId"],
                "token": new_token,
                "refreshedAt": datetime.now(timezone.utc).isoformat(),
            },
            private=True,
        )
        client = ThreadsClient(token_record["userId"], new_token)
        log.info("토큰을 갱신했습니다")

    return client


def main() -> int:
    config.LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=config.LOG_PATH,
        level=logging.INFO,
        format="%(asctime)s approve %(levelname)s %(message)s",
    )

    token, chat_id = config.load_telegram_credentials()
    telegram = Telegram(token, chat_id)

    try:
        with exclusive_lock(config.STATE_DIR):
            state = State(config.STATE_DIR)
            pending = state.read_json("pending.json", None)
            if pending is None:
                return 0
            return run(
                state=state,
                telegram=telegram,
                threads=_load_client(state, telegram),
                recompose=_recompose(state, telegram, pending["slug"]),
            )
    except LockBusy:
        return 0
    except Exception as exc:  # noqa: BLE001 — 조용히 죽지 않는다
        log.exception("approve 실패")
        telegram.notify(f"🔴 Threads 승인 처리 실패 — {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: 테스트가 통과하는지 확인한다**

Run: `cd scripts/threads && python3 -m pytest tests/test_approve_entry.py -v`
Expected: PASS — 11 passed

- [ ] **Step 5: 전체 테스트를 돌린다**

Run: `cd scripts/threads && python3 -m pytest tests -v`
Expected: PASS — 92 passed

- [ ] **Step 6: 실행 권한을 주고 커밋한다**

```bash
chmod +x scripts/threads/approve.py
git add scripts/threads/approve.py scripts/threads/tests/test_approve_entry.py
git commit -m "feat: Threads 승인 폴링 진입점"
```

---

## Task 11: launchd 등록 파일

**Files:**
- Create: `scripts/threads/launchd/com.zihado.threads-compose.plist`
- Create: `scripts/threads/launchd/com.zihado.threads-approve.plist`
- Modify: `scripts/launchd/com.zihado.portfolio-update.plist` (옛 저장소 경로 수정)

> **파이썬 경로 주의**: `/usr/bin/python3`은 이 맥에서 3.9.6이고 pytest 도 없다.
> 실제로 쓰는 것은 `/Library/Frameworks/Python.framework/Versions/3.13/bin/python3` 이다
> (`python3 -c "import sys; print(sys.executable)"` 로 확인). launchd 는 로그인 셸의
> PATH 를 쓰지 않으므로 plist 에 절대 경로를 박아야 한다.
> 나중에 파이썬을 올리면 두 plist 의 경로를 함께 고쳐야 한다.

- [ ] **Step 1: 초안 생성 잡을 만든다**

Create `scripts/threads/launchd/com.zihado.threads-compose.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.zihado.threads-compose</string>

  <key>ProgramArguments</key>
  <array>
    <string>/Library/Frameworks/Python.framework/Versions/3.13/bin/python3</string>
    <string>/Users/zihado/work/playground/code.zihado.com/scripts/threads/compose.py</string>
  </array>

  <!-- 매일 08:00 (KST, 로컬 시간) -->
  <key>StartCalendarInterval</key>
  <dict>
    <key>Hour</key>
    <integer>8</integer>
    <key>Minute</key>
    <integer>0</integer>
  </dict>

  <key>StandardOutPath</key>
  <string>/Users/zihado/Library/Logs/threads-poster.launchd.log</string>
  <key>StandardErrorPath</key>
  <string>/Users/zihado/Library/Logs/threads-poster.launchd.log</string>
</dict>
</plist>
```

- [ ] **Step 2: 승인 폴링 잡을 만든다**

Create `scripts/threads/launchd/com.zihado.threads-approve.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.zihado.threads-approve</string>

  <key>ProgramArguments</key>
  <array>
    <string>/Library/Frameworks/Python.framework/Versions/3.13/bin/python3</string>
    <string>/Users/zihado/work/playground/code.zihado.com/scripts/threads/approve.py</string>
  </array>

  <!-- 5분마다. pending 이 없으면 즉시 종료한다. -->
  <key>StartInterval</key>
  <integer>300</integer>

  <key>StandardOutPath</key>
  <string>/Users/zihado/Library/Logs/threads-poster.launchd.log</string>
  <key>StandardErrorPath</key>
  <string>/Users/zihado/Library/Logs/threads-poster.launchd.log</string>
</dict>
</plist>
```

- [ ] **Step 3: 기존 plist 의 옛 경로를 고친다**

Modify `scripts/launchd/com.zihado.portfolio-update.plist:14` — `ProgramArguments` 두 번째 항목:

```xml
    <string>/Users/zihado/work/playground/code.zihado.com/scripts/auto-update.sh</string>
```

(현재 값은 `/Users/zihado/work/playground/vibe-coding/scripts/auto-update.sh` 로,
저장소 이름을 바꾸기 전 경로다.)

- [ ] **Step 4: plist 문법을 검증한다**

```bash
plutil -lint scripts/threads/launchd/com.zihado.threads-compose.plist
plutil -lint scripts/threads/launchd/com.zihado.threads-approve.plist
plutil -lint scripts/launchd/com.zihado.portfolio-update.plist
```

Expected: 세 파일 모두 `OK`

- [ ] **Step 5: 커밋한다**

```bash
git add scripts/threads/launchd scripts/launchd/com.zihado.portfolio-update.plist
git commit -m "feat: Threads 포스터 launchd 등록 파일

기존 portfolio-update plist 의 옛 저장소 경로도 함께 수정"
```

---

## Task 12: 운영 문서

**Files:**
- Create: `scripts/threads/README.md`
- Modify: `README.md` (파일 구성 표에 한 줄 추가)

- [ ] **Step 1: 운영 문서를 쓴다**

Create `scripts/threads/README.md`:

````markdown
# Threads 일일 자동 포스팅

`projects.json`의 프로젝트를 매일 하나씩 골라 문구를 만들고,
텔레그램으로 승인을 받아 Threads에 게시합니다.

- 매일 **08:00** — `compose.py`가 초안을 만들어 텔레그램으로 보냅니다
- **5분마다** — `approve.py`가 버튼 응답을 확인해 게시/건너뛰기/재작성을 처리합니다

설계 문서: `docs/superpowers/specs/2026-08-09-threads-daily-poster-design.md`

## 최초 설정

### 1. Threads 앱과 토큰 (수동, 1회)

1. https://developers.facebook.com/apps 에서 앱을 만들고 **Threads API** 제품을 추가합니다
2. 권한에 `threads_basic`, `threads_content_publish`를 넣습니다
3. Threads 계정으로 인증해 **장기 토큰(long-lived token)**을 발급받습니다
4. 사용자 ID를 조회합니다:

   ```bash
   curl -s "https://graph.threads.net/v1.0/me?fields=id&access_token=<TOKEN>"
   ```

5. 상태 디렉토리에 토큰을 저장합니다:

   ```bash
   mkdir -p ~/.local/state/threads-poster
   cat > ~/.local/state/threads-poster/token.json <<'JSON'
   {
     "userId": "<위에서 받은 id>",
     "token": "<장기 토큰>",
     "refreshedAt": "2026-08-09T00:00:00+00:00"
   }
   JSON
   chmod 600 ~/.local/state/threads-poster/token.json
   ```

토큰은 60일마다 만료되지만, `approve.py`가 30일이 지나면 자동으로 갱신합니다.
갱신에 실패하면 텔레그램으로 알림이 옵니다.

### 2. 텔레그램

`~/.env`의 `TELEGRAM_BOT_TOKEN` / `AUTHORIZED_CHAT_ID`를 그대로 씁니다
(`scripts/auto-update.sh`와 같은 값).

> **주의**: 봇 토큰 하나당 `getUpdates`는 한 프로세스만 쓸 수 있습니다.
> 같은 봇으로 다른 폴링 봇을 돌리면 충돌합니다. 그럴 땐 별도 봇을 발급하세요.

### 3. launchd 등록

```bash
cp scripts/threads/launchd/*.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.zihado.threads-compose.plist
launchctl load ~/Library/LaunchAgents/com.zihado.threads-approve.plist
launchctl list | grep threads
```

## 운영

**초안을 직접 만들어보기 (전송 없음)**

```bash
python3 scripts/threads/compose.py --dry-run
python3 scripts/threads/compose.py --dry-run --project law
```

**로그**

```bash
tail -f ~/Library/Logs/threads-poster.log
```

**상태 확인**

```bash
ls -la ~/.local/state/threads-poster/
python3 -c "import json; print(len(json.load(open('$HOME/.local/state/threads-poster/posted.json'))))"
```

**대기 중인 초안 취소**

```bash
rm ~/.local/state/threads-poster/pending.json
```

**중단**

```bash
launchctl unload ~/Library/LaunchAgents/com.zihado.threads-compose.plist
launchctl unload ~/Library/LaunchAgents/com.zihado.threads-approve.plist
```

## 테스트

```bash
cd scripts/threads && python3 -m pytest tests -v
```

네트워크를 타지 않습니다. 실제 게시는 자동 테스트하지 않습니다.

## 동작 규칙

- 이미 소개한 프로젝트는 같은 회차에 다시 나오지 않습니다. 59개를 다 돌면 2회차가
  시작되고, 이때는 1회차 본문을 참고해 다른 각도로 씁니다
- 어제 초안이 승인 대기 중이면 오늘 초안을 만들지 않습니다 (초안이 쌓이지 않도록)
- 게시 중 실패하면 `pending.json`에 `creationId`가 남아, 다음 폴링에서
  **게시만** 재시도합니다. 같은 글이 두 번 올라가지 않습니다
- 이 시스템은 저장소를 `projects.json` 읽기 전용으로만 씁니다. 상태를 저장소에 쓰면
  `auto-update.sh`의 "워킹 트리가 더러우면 건너뛴다" 가드에 걸립니다
````

- [ ] **Step 2: 저장소 README 의 파일 구성 표에 한 줄 추가한다**

Modify `README.md` — 파일 구성 표 마지막 행 뒤에 다음을 추가:

```markdown
| `scripts/threads/` | Threads 일일 자동 포스팅 — 매일 프로젝트 하나를 소개 ([설명](scripts/threads/README.md)) |
```

- [ ] **Step 3: 커밋한다**

```bash
git add scripts/threads/README.md README.md
git commit -m "docs: Threads 자동 포스팅 운영 문서"
```

---

## Task 13: 첫 실행 검증 (수동)

자동 테스트로 덮을 수 없는 구간이다. 옆에서 지켜보며 진행한다.

- [ ] **Step 1: 전체 테스트가 통과하는지 확인한다**

Run: `cd scripts/threads && python3 -m pytest tests -v`
Expected: PASS — 92 passed

- [ ] **Step 2: 문구 품질을 눈으로 확인한다**

```bash
python3 scripts/threads/compose.py --dry-run
```

같은 명령을 3~4번 돌려 서로 다른 프로젝트의 문구를 본다. 확인할 것:

- 500자를 넘지 않는가
- 톤이 자랑이 아니라 "배운 것" 중심인가
- 전문 용어가 풀어져 있는가
- `stack` 나열이나 `slug` 노출이 없는가

기대에 못 미치면 **`compose-prompt.md`만 고친다.** 코드는 건드릴 필요가 없다.

- [ ] **Step 3: `live` 링크가 없는 프로젝트도 확인한다**

```bash
python3 -c "
import json
d = json.load(open('projects.json'))
print([p['slug'] for c in d['categories'] for p in c['projects'] if 'live' not in p])
"
```

출력된 slug 중 하나로 dry-run 을 돌려 링크 없이도 문장이 자연스럽게 끝나는지 본다:

```bash
python3 scripts/threads/compose.py --dry-run --project <slug>
```

- [ ] **Step 4: 텔레그램 전송을 확인한다**

```bash
python3 scripts/threads/compose.py
```

폰에서 확인할 것: 초안 본문이 오는가, 버튼 3개가 보이는가, 글자 수 표시가 맞는가.

- [ ] **Step 5: 실제 게시를 확인한다**

`✅ 게시`를 누르고 5분 안에:

```bash
tail -20 ~/Library/Logs/threads-poster.log
cat ~/.local/state/threads-poster/posted.json
```

Threads 앱에서 글이 올라갔는지, 텔레그램 메시지가 "✅ 게시했습니다"로 바뀌고
버튼이 사라졌는지 확인한다.

- [ ] **Step 6: 건너뛰기와 재작성도 한 번씩 확인한다**

```bash
python3 scripts/threads/compose.py --project <다른 slug>
```

`🔄 다시`를 눌러 새 초안이 **같은 프로젝트**로 오는지 확인하고,
다시 만든 초안에서 `❌ 건너뛰기`를 눌러 `posted.json`에 `"skipped": true`가
기록되는지 확인한다.

- [ ] **Step 7: launchd 를 등록하고 다음 날 08:00 을 기다린다**

```bash
cp scripts/threads/launchd/*.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.zihado.threads-compose.plist
launchctl load ~/Library/LaunchAgents/com.zihado.threads-approve.plist
launchctl list | grep threads
```

Expected: 두 잡이 목록에 보이고 마지막 종료 코드가 `0`

- [ ] **Step 8: 검증 결과를 커밋한다**

`compose-prompt.md`를 손봤다면:

```bash
git add scripts/threads/compose-prompt.md
git commit -m "fix: Threads 문구 지침 실사용 반영"
```
