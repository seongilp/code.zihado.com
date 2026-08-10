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


def _notify_safely(telegram, text: str) -> None:
    """마지막 방어선에서 쓰는 알림.

    notify 자체가 네트워크 호출이라, 장애 원인이 텔레그램이면 여기서 또 던진다.
    그러면 예외가 main 밖으로 나가 아무도 안 읽는 launchd 로그에만 남는다.
    """
    try:
        telegram.notify(text)
    except Exception:  # noqa: BLE001
        log.exception("텔레그램 알림마저 실패 — %s", text)


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
        # 08:00 실행은 놓치면 launchd 가 다시 부르지 않는다. 그날 포스팅이
        # 통째로 사라지므로 조용히 넘어가면 안 된다. approve 가 게시 중이거나
        # 재작성으로 claude 를 돌리는 동안 겹칠 수 있다.
        log.info("다른 인스턴스가 실행 중 — 건너뜁니다")
        _notify_safely(
            telegram,
            "🟡 Threads 초안을 건너뛰었습니다 — 승인 처리가 진행 중이라 잠금이 잡혀 있었어요.\n"
            "직접 돌리려면: python3 scripts/threads/compose.py",
        )
        return 0
    except Exception as exc:  # noqa: BLE001 — 조용히 죽지 않는다
        log.exception("compose 실패")
        _notify_safely(telegram, f"🔴 Threads 초안 실패 — {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
