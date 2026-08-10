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

    # 출력 형식 지시는 맨 뒤에 한 번 더 박는다. 앞에만 두면 프로젝트 JSON 을
    # 읽는 사이에 잊고 "다음은 최종 본문입니다" 같은 머리말을 붙인다.
    # sanitize 는 펜스와 따옴표만 벗기지 이런 문장은 못 걸러낸다.
    blocks.append(
        "## 마지막 확인\n\n"
        "지금부터 출력하는 첫 글자가 그대로 게시됩니다.\n"
        "`다음은 ...입니다`, `N자입니다`, `최종 본문입니다` 같은 설명을 앞이나 뒤에\n"
        "붙이지 마세요. 본문만 출력하세요."
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
