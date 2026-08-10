from datetime import datetime, timedelta

import pytest

from approve import CONTAINER_TTL_HOURS, MAX_PUBLISH_ATTEMPTS, run
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


def _now():
    return datetime.now().astimezone().isoformat()


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
    return Callback(id="cb1", action="publish", slug="law")


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
    callback = Callback(id="cb", action="skip", slug="law")
    _, state, _, threads = call(tmp_path, callbacks=[callback], state=state)
    assert threads.created == []
    posted = state.read_json("posted.json", [])
    assert posted[0]["skipped"] is True
    assert state.read_json("pending.json", None) is None


def test_retry_callback_clears_pending_and_recomposes(tmp_path):
    state = State(tmp_path / "state")
    pending(state)
    calls = []
    callback = Callback(id="cb", action="retry", slug="law")
    call(tmp_path, callbacks=[callback], state=state, recompose=lambda: calls.append(1))
    assert calls == [1]


def test_callback_for_a_different_project_is_ignored(tmp_path):
    state = State(tmp_path / "state")
    pending(state)
    stale = Callback(id="cb", action="publish", slug="asm")
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


def test_container_creation_records_when_it_happened(tmp_path):
    state = State(tmp_path / "state")
    pending(state)
    call(
        tmp_path,
        callbacks=[approve_callback()],
        state=state,
        threads=FakeThreads(publish_fails=True),
    )
    assert state.read_json("pending.json", None)["containerCreatedAt"]


def test_a_publish_failure_records_an_attempt(tmp_path):
    state = State(tmp_path / "state")
    pending(state)
    call(
        tmp_path,
        callbacks=[approve_callback()],
        state=state,
        threads=FakeThreads(publish_fails=True),
    )
    assert state.read_json("pending.json", None)["publishAttempts"] == 1


def test_repeated_publish_failures_eventually_give_up(tmp_path):
    """상한이 없으면 5분마다 알림이 영원히 쌓이고 새 초안도 안 만들어진다."""
    state = State(tmp_path / "state")
    pending(state, creationId="container-1", containerCreatedAt=_now())

    for _ in range(MAX_PUBLISH_ATTEMPTS + 2):
        if state.read_json("pending.json", None) is None:
            break
        call(tmp_path, state=state, threads=FakeThreads(publish_fails=True))

    assert state.read_json("pending.json", None) is None
    record = state.read_json("posted.json", [])[-1]
    assert record["skipped"] is True
    assert record["abandoned"]


def test_giving_up_tells_the_user_how_to_recover(tmp_path):
    state = State(tmp_path / "state")
    pending(state, creationId="container-1", publishAttempts=MAX_PUBLISH_ATTEMPTS - 1)
    _, _, telegram, _ = call(
        tmp_path, state=state, threads=FakeThreads(publish_fails=True)
    )
    assert any("--project law" in notice for notice in telegram.notices)


def test_an_expired_container_is_abandoned_without_calling_threads(tmp_path):
    state = State(tmp_path / "state")
    stale = (
        datetime.now().astimezone() - timedelta(hours=CONTAINER_TTL_HOURS + 1)
    ).isoformat()
    pending(state, creationId="container-1", containerCreatedAt=stale)
    _, state, _, threads = call(tmp_path, state=state)
    assert threads.published == []
    assert state.read_json("pending.json", None) is None


def test_a_draft_already_in_posted_is_not_published_again(tmp_path):
    """게시 후 pending 삭제 전에 죽거나 전원이 나간 경우다."""
    state = State(tmp_path / "state")
    state.write_json(
        "posted.json", [{"slug": "law", "round": 1, "threadId": "thread-1"}]
    )
    pending(state, creationId="container-1")
    _, state, telegram, threads = call(tmp_path, state=state)
    assert threads.published == []
    assert threads.created == []
    assert state.read_json("pending.json", None) is None
    assert len(state.read_json("posted.json", [])) == 1
    assert "이미 게시" in telegram.resolved[0][1]
