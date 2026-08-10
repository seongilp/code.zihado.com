"""Threads Graph API. HTTP 만 담당하고 트랜스포트는 주입받는다."""

from __future__ import annotations

import json
import time
import urllib.error
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


def _decode_error_body(exc: urllib.error.HTTPError) -> dict[str, Any]:
    """오류 응답의 JSON 바디를 살려낸다.

    Threads 는 오류를 400 + JSON 바디로 돌려준다. HTTPError 를 그대로 흘리면
    텔레그램에는 "HTTP Error 400: Bad Request" 만 남고, 진짜 이유가 담긴
    error.message 는 버려진다. 이 시스템의 유일한 관측 수단이 텔레그램이라
    그러면 원인을 알 방법이 없다.
    """
    try:
        raw = exc.read().decode("utf-8")
    except Exception:  # noqa: BLE001 — 바디를 못 읽어도 상태코드는 알려야 한다
        raw = ""
    try:
        payload = json.loads(raw)
    except ValueError:
        payload = None
    if isinstance(payload, dict) and "error" in payload:
        return payload
    return {"error": {"message": f"HTTP {exc.code} — {raw[:300] or exc.reason}"}}


def _http_transport() -> Transport:
    def call(method: str, url: str, params: dict[str, Any]) -> dict[str, Any]:
        encoded = urllib.parse.urlencode(params)
        if method == "GET":
            request = urllib.request.Request(f"{url}?{encoded}", method="GET")
        else:
            request = urllib.request.Request(url, data=encoded.encode("utf-8"), method="POST")
        try:
            with urllib.request.urlopen(request, timeout=_TIMEOUT_SECONDS) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            return _decode_error_body(exc)

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
