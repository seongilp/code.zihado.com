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
