"""LLM 이 뱉은 문자열을 게시 가능한 본문으로 정리한다."""

from __future__ import annotations

import re

MAX_LENGTH = 500  # Threads 텍스트 게시물 상한

_FENCE = re.compile(r"\A```[A-Za-z]*\n(.*)\n```\Z", re.DOTALL)
_BLANK_LINES = re.compile(r"\n{3,}")
_QUOTE_PAIRS = (
    '\"\"',  # straight double quotes
    "\''",  # straight single quotes
    '\u201c\u201d',  # curly double quotes
    '\u2018\u2019',  # curly single quotes
)


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
