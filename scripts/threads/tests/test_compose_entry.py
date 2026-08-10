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
