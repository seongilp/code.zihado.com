"""LLM 이 뱉은 문자열을 게시 가능한 본문으로 정리한다."""

from __future__ import annotations

import re

# Threads 텍스트 게시물 상한. 문서상 "500자" 기준으로 파이썬 len() 을 쓴다.
# 이모지가 UTF-16 기준으로 세어질 가능성이 있지만, 작성 지침이 이모지를
# 2개 이하로 제한하므로 실제 차이가 없다고 보고 넘어간다. 혹시 게시 단계에서
# 길이로 거절당하면 pending 이 남으므로 사람이 고쳐 다시 올릴 수 있다.
MAX_LENGTH = 500

_FENCE_BLOCK = re.compile(r"\A```[^\n]*\n(.*?)\n?```\Z", re.DOTALL)
_FENCE_INLINE = re.compile(r"\A```(.*?)```\Z", re.DOTALL)
_BLANK_LINES = re.compile(r"\n{3,}")
# 곡선 따옴표는 이스케이프로 적는다. 그대로 적으면 편집 과정에서
# 곧은 따옴표로 바뀌어 조용히 동작이 깨진다.
_QUOTE_PAIRS = (
    ('"', '"'),
    ("'", "'"),
    ("“", "”"),
    ("‘", "’"),
)
_MAX_UNWRAP_PASSES = 5


class EmptyTextError(ValueError):
    """정리하고 나니 남은 내용이 없다."""


class TooLongError(ValueError):
    def __init__(self, text: str, length: int) -> None:
        super().__init__(f"{length}자 — 상한 {MAX_LENGTH}자를 넘었습니다")
        self.text = text
        self.length = length


def _unwrap_fence(text: str) -> str:
    match = _FENCE_BLOCK.match(text) or _FENCE_INLINE.match(text)
    return match.group(1).strip() if match else text


def _unwrap_quotes(text: str) -> str:
    """전체가 하나의 인용 덩어리일 때만 벗긴다.

    '"안녕" 그리고 "잘가"' 처럼 양 끝이 우연히 따옴표인 경우까지 벗기면
    본문이 조용히 망가진다. 따옴표 하나가 남는 편이 낫다.
    """
    for opening, closing in _QUOTE_PAIRS:
        if len(text) < 2 or not text.startswith(opening) or not text.endswith(closing):
            continue
        inner = text[1:-1]
        if opening in inner or closing in inner:
            continue
        return inner.strip()
    return text


def clean(raw: str) -> str:
    text = raw.replace("\r\n", "\n").strip()

    # 펜스 안에 따옴표, 따옴표 안에 펜스가 겹쳐 오기도 한다.
    # 더 벗길 게 없을 때까지 돌리되, 무한 루프는 막는다.
    for _ in range(_MAX_UNWRAP_PASSES):
        stripped = _unwrap_quotes(_unwrap_fence(text)).strip()
        if stripped == text:
            break
        text = stripped

    return _BLANK_LINES.sub("\n\n", text)


def validate(text: str) -> str:
    if not text.strip():
        raise EmptyTextError("빈 문구입니다")
    if len(text) > MAX_LENGTH:
        raise TooLongError(text, len(text))
    return text
