#!/usr/bin/env python3
"""5분마다 — 텔레그램 버튼 응답을 확인해 게시하거나 건너뛴다."""

from __future__ import annotations

import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from compose import run as compose_run
from poster import config
from poster.composer import claude_runner
from poster.state import LockBusy, State, exclusive_lock
from poster.telegram import Telegram
from poster.threads_api import ThreadsClient, ThreadsError, needs_refresh

log = logging.getLogger("threads.approve")

# 게시 실패는 재시도하되 영원히는 아니다. 상한이 없으면 5분마다 실패 알림이
# 하루 288건 쌓이고, pending 이 안 사라져 새 초안도 다시는 만들어지지 않는다.
MAX_PUBLISH_ATTEMPTS = 6
# Threads 컨테이너 수명. 이걸 넘기면 이 creationId 로는 절대 게시할 수 없다.
CONTAINER_TTL_HOURS = 24


def _already_published(state, pending) -> bool:
    """이미 올라간 글인지 확인한다.

    게시에 성공하고 posted.json 까지 썼는데 pending 삭제 전에 죽으면
    (혹은 전원이 나가 unlink 가 되돌아가면) 다음 실행이 같은 글을
    또 올리려 든다. 여기서 막는다.
    """
    return any(
        record.get("slug") == pending["slug"]
        and record.get("round") == pending["round"]
        and record.get("threadId")
        for record in state.read_json("posted.json", [])
    )


def _container_expired(pending) -> bool:
    stamp = pending.get("containerCreatedAt")
    if not stamp:
        return False
    try:
        created = datetime.fromisoformat(stamp)
    except ValueError:
        return False
    return datetime.now().astimezone() - created >= timedelta(hours=CONTAINER_TTL_HOURS)


def _abandon(state, telegram, pending, reason: str) -> None:
    """포기하고 빠져나온다.

    실제로 올라갔는지 알 수 없으므로 skipped 로 기록해 다시 뽑히지 않게 한다.
    중복 게시가 한 건 누락보다 나쁘다. 누락은 --project 로 언제든 만회할 수 있다.
    """
    posted = state.read_json("posted.json", [])
    posted.append(
        {
            "slug": pending["slug"],
            "round": pending["round"],
            "postedAt": datetime.now().astimezone().isoformat(),
            "skipped": True,
            "abandoned": reason,
        }
    )
    state.write_json("posted.json", posted)
    state.delete("pending.json")
    telegram.notify(
        f"🔴 Threads 게시를 포기했습니다 — {pending['slug']}\n"
        f"이유: {reason}\n\n"
        "Threads 앱에서 실제로 올라갔는지 직접 확인해 주세요.\n"
        "안 올라갔다면: python3 scripts/threads/compose.py --project "
        f"{pending['slug']}\n\n"
        "내일 초안은 정상적으로 옵니다."
    )


def _finish_publish(state, telegram, threads, pending) -> None:
    """컨테이너를 만들고 게시한다. creationId 가 이미 있으면 게시만 재시도한다."""
    if _already_published(state, pending):
        state.delete("pending.json")
        telegram.resolve(
            pending["telegramMessageId"], f"✅ 이미 게시된 글입니다 — {pending['slug']}"
        )
        return

    creation_id = pending.get("creationId")
    if not creation_id:
        creation_id = threads.create_container(pending["text"])
        # 게시 전에 저장한다. 여기서 죽어도 컨테이너를 두 번 만들지 않는다.
        state.write_json(
            "pending.json",
            {
                **pending,
                "creationId": creation_id,
                "containerCreatedAt": datetime.now().astimezone().isoformat(),
            },
        )

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


def _resume_publish(state, telegram, threads, pending) -> int:
    """컨테이너까지 만들어 둔 건을 마저 게시한다. 영원히 매달리지는 않는다."""
    if _container_expired(pending):
        _abandon(
            state,
            telegram,
            pending,
            f"컨테이너가 {CONTAINER_TTL_HOURS}시간을 넘겨 만료됐습니다",
        )
        return 1

    try:
        _finish_publish(state, telegram, threads, pending)
    except ThreadsError as exc:
        attempts = pending.get("publishAttempts", 0) + 1
        if attempts >= MAX_PUBLISH_ATTEMPTS:
            _abandon(state, telegram, pending, f"게시가 {attempts}번 연속 실패 — {exc}")
            return 1
        state.write_json("pending.json", {**pending, "publishAttempts": attempts})
        telegram.notify(
            f"🔴 Threads 게시 재시도 실패 ({attempts}/{MAX_PUBLISH_ATTEMPTS}) — {exc}"
        )
        return 1
    return 0


def run(*, state, telegram, threads, recompose) -> int:
    pending = state.read_json("pending.json", None)
    if pending is None:
        return 0

    # 지난번에 컨테이너까지 만들고 실패한 건이면 승인을 기다리지 않고 게시를 마저 끝낸다.
    if pending.get("creationId"):
        return _resume_publish(state, telegram, threads, pending)

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
                # 컨테이너까지 갔다면 pending 에 creationId 가 이미 저장돼 있다.
                # 그 위에 시도 횟수를 얹어야 다음 폴링이 상한을 셀 수 있다.
                current = state.read_json("pending.json", None) or pending
                state.write_json("pending.json", {**current, "publishAttempts": 1})
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


def refresh_token_if_stale(state, telegram) -> dict | None:
    """30일이 넘었으면 토큰을 갱신한다. 갱신된(또는 그대로인) 기록을 돌려준다.

    대기 중인 초안이 없을 때도 부른다. 토큰은 초안과 무관하게 늙기 때문에,
    승인 경로에서만 갱신하면 며칠 조용한 사이에 만료될 수 있다.
    token.json 이 아직 없으면(최초 설정 전) 조용히 넘어간다.
    """
    token_record = state.read_json("token.json", None)
    if token_record is None:
        return None
    if not needs_refresh(token_record.get("refreshedAt"), datetime.now(timezone.utc)):
        return token_record

    client = ThreadsClient(token_record["userId"], token_record["token"])
    try:
        new_token = client.refresh_token()
    except ThreadsError as exc:
        telegram.notify(
            f"🔴 Threads 토큰 갱신 실패 — {exc}\n"
            "수동 재발급이 필요합니다: scripts/threads/README.md"
        )
        # 아직 만료 전이다(수명 60일 중 30일 시점). 옛 토큰으로 계속 간다.
        return token_record

    refreshed = {
        "userId": token_record["userId"],
        "token": new_token,
        "refreshedAt": datetime.now(timezone.utc).isoformat(),
    }
    # 새 토큰을 쓰기 전에 먼저 저장한다. 순서가 반대면 갱신은 했는데
    # 기록이 없어 다음 실행이 죽은 옛 토큰을 쓰게 된다.
    state.write_json("token.json", refreshed, private=True)
    log.info("토큰을 갱신했습니다")
    return refreshed


def _load_client(state, telegram) -> ThreadsClient:
    token_record = refresh_token_if_stale(state, telegram)
    if token_record is None:
        raise RuntimeError(
            "token.json 이 없습니다. scripts/threads/README.md 의 토큰 발급 절차를 보세요."
        )
    return ThreadsClient(token_record["userId"], token_record["token"])


def _notify_safely(telegram, text: str) -> None:
    """마지막 방어선에서 쓰는 알림.

    notify 자체가 네트워크 호출이라, 장애 원인이 텔레그램이면 여기서 또 던진다.
    그러면 예외가 main 밖으로 나가 아무도 안 읽는 launchd 로그에만 남는다.
    """
    try:
        telegram.notify(text)
    except Exception:  # noqa: BLE001
        log.exception("텔레그램 알림마저 실패 — %s", text)


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
                # 할 일이 없어도 토큰 나이는 확인하고 간다.
                refresh_token_if_stale(state, telegram)
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
        _notify_safely(telegram, f"🔴 Threads 승인 처리 실패 — {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
