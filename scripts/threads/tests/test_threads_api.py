from datetime import datetime, timedelta, timezone

import pytest

from poster.threads_api import (
    REFRESH_AFTER_DAYS,
    ThreadsClient,
    ThreadsError,
    needs_refresh,
)


class FakeTransport:
    def __init__(self, responses):
        self.calls = []
        self._responses = list(responses)

    def __call__(self, method, url, params):
        self.calls.append((method, url, params))
        result = self._responses.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


def make(responses):
    transport = FakeTransport(responses)
    slept = []
    client = ThreadsClient(
        "user-1", "token-1", transport=transport, sleep=slept.append
    )
    return client, transport, slept


def test_create_container_returns_the_creation_id():
    client, _, _ = make([{"id": "container-9"}])
    assert client.create_container("본문") == "container-9"


def test_create_container_sends_text_media_type_and_the_body():
    client, transport, _ = make([{"id": "c"}])
    client.create_container("본문")
    method, url, params = transport.calls[0]
    assert method == "POST"
    assert url.endswith("/user-1/threads")
    assert params["media_type"] == "TEXT"
    assert params["text"] == "본문"
    assert params["access_token"] == "token-1"


def test_publish_returns_the_thread_id():
    client, _, _ = make([{"id": "thread-7"}])
    assert client.publish("container-9") == "thread-7"


def test_publish_waits_before_calling_the_api():
    client, _, slept = make([{"id": "thread-7"}])
    client.publish("container-9")
    assert slept == [client.publish_delay_seconds]


def test_publish_sends_the_creation_id():
    client, transport, _ = make([{"id": "t"}])
    client.publish("container-9")
    _, url, params = transport.calls[0]
    assert url.endswith("/user-1/threads_publish")
    assert params["creation_id"] == "container-9"


def test_api_error_payload_is_raised():
    client, _, _ = make([{"error": {"message": "Invalid OAuth access token"}}])
    with pytest.raises(ThreadsError, match="Invalid OAuth access token"):
        client.create_container("본문")


def test_missing_id_in_response_is_an_error():
    client, _, _ = make([{}])
    with pytest.raises(ThreadsError):
        client.create_container("본문")


def test_refresh_token_returns_the_new_token():
    client, transport, _ = make([{"access_token": "token-2", "expires_in": 5184000}])
    assert client.refresh_token() == "token-2"
    method, url, params = transport.calls[0]
    assert method == "GET"
    assert url.endswith("/refresh_access_token")
    assert params["grant_type"] == "th_refresh_token"


def test_needs_refresh_is_false_for_a_fresh_token():
    now = datetime(2026, 8, 9, tzinfo=timezone.utc)
    recent = (now - timedelta(days=REFRESH_AFTER_DAYS - 1)).isoformat()
    assert needs_refresh(recent, now) is False


def test_needs_refresh_is_true_past_the_threshold():
    now = datetime(2026, 8, 9, tzinfo=timezone.utc)
    old = (now - timedelta(days=REFRESH_AFTER_DAYS + 1)).isoformat()
    assert needs_refresh(old, now) is True


def test_needs_refresh_is_true_when_the_timestamp_is_missing():
    assert needs_refresh(None, datetime(2026, 8, 9, tzinfo=timezone.utc)) is True


def test_needs_refresh_is_true_when_the_timestamp_is_unparseable():
    assert needs_refresh("어제", datetime(2026, 8, 9, tzinfo=timezone.utc)) is True
