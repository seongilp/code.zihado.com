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
