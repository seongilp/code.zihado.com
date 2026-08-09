import json

import pytest

from poster.telegram import Callback, Telegram, TelegramError


class FakeTransport:
    """(method, params) 를 기록하고 미리 정한 응답을 돌려준다."""

    def __init__(self, responses=None):
        self.calls = []
        self.responses = responses or {}

    def __call__(self, method, params):
        self.calls.append((method, params))
        return self.responses.get(method, {"ok": True, "result": {}})


def make(responses=None):
    transport = FakeTransport(responses)
    return Telegram("bot-token", "12345", transport=transport), transport


def test_send_draft_returns_message_id():
    telegram, _ = make({"sendMessage": {"ok": True, "result": {"message_id": 4521}}})
    assert telegram.send_draft(slug="law", text="본문") == 4521


def test_send_draft_targets_the_authorized_chat():
    telegram, transport = make({"sendMessage": {"ok": True, "result": {"message_id": 1}}})
    telegram.send_draft(slug="law", text="본문")
    _, params = transport.calls[0]
    assert params["chat_id"] == "12345"


def test_send_draft_includes_three_buttons_with_namespaced_callback_data():
    telegram, transport = make({"sendMessage": {"ok": True, "result": {"message_id": 1}}})
    telegram.send_draft(slug="law", text="본문")
    _, params = transport.calls[0]
    row = json.loads(params["reply_markup"])["inline_keyboard"][0]
    assert [button["callback_data"] for button in row] == [
        "threads:publish:law",
        "threads:retry:law",
        "threads:skip:law",
    ]


def test_send_draft_shows_the_warning_when_given():
    telegram, transport = make({"sendMessage": {"ok": True, "result": {"message_id": 1}}})
    telegram.send_draft(slug="law", text="본문", warning="길이 초과")
    _, params = transport.calls[0]
    assert "길이 초과" in params["text"]


def test_send_draft_body_contains_the_post_text():
    telegram, transport = make({"sendMessage": {"ok": True, "result": {"message_id": 1}}})
    telegram.send_draft(slug="law", text="오늘의 본문")
    _, params = transport.calls[0]
    assert "오늘의 본문" in params["text"]


def test_notify_sends_a_plain_message():
    telegram, transport = make()
    telegram.notify("알림")
    method, params = transport.calls[0]
    assert method == "sendMessage"
    assert params["text"] == "알림"
    assert "reply_markup" not in params


def test_poll_callbacks_parses_updates_and_advances_the_offset():
    telegram, transport = make(
        {
            "getUpdates": {
                "ok": True,
                "result": [
                    {
                        "update_id": 100,
                        "callback_query": {
                            "id": "cb1",
                            "data": "threads:publish:law",
                            "message": {"message_id": 4521},
                        },
                    }
                ],
            }
        }
    )
    callbacks, offset = telegram.poll_callbacks(0)
    assert callbacks == [Callback(id="cb1", action="publish", slug="law", message_id=4521)]
    assert offset == 101


def test_poll_callbacks_passes_the_offset_through():
    telegram, transport = make({"getUpdates": {"ok": True, "result": []}})
    telegram.poll_callbacks(77)
    _, params = transport.calls[0]
    assert params["offset"] == 77


def test_poll_callbacks_keeps_the_offset_when_nothing_arrived():
    telegram, _ = make({"getUpdates": {"ok": True, "result": []}})
    callbacks, offset = telegram.poll_callbacks(77)
    assert callbacks == []
    assert offset == 77


def test_poll_callbacks_ignores_updates_from_other_features():
    telegram, _ = make(
        {
            "getUpdates": {
                "ok": True,
                "result": [
                    {"update_id": 5, "message": {"text": "안녕"}},
                    {
                        "update_id": 6,
                        "callback_query": {
                            "id": "cb",
                            "data": "other:thing:x",
                            "message": {"message_id": 9},
                        },
                    },
                ],
            }
        }
    )
    callbacks, offset = telegram.poll_callbacks(0)
    assert callbacks == []
    assert offset == 7  # 처리하지 않아도 offset 은 넘긴다


def test_resolve_edits_the_message_and_drops_the_buttons():
    telegram, transport = make()
    telegram.resolve(4521, "게시했습니다")
    method, params = transport.calls[0]
    assert method == "editMessageText"
    assert params["message_id"] == 4521
    assert params["text"] == "게시했습니다"
    assert json.loads(params["reply_markup"]) == {"inline_keyboard": []}


def test_answer_callback_acknowledges_the_button_press():
    telegram, transport = make()
    telegram.answer_callback("cb1", "처리 중")
    method, params = transport.calls[0]
    assert method == "answerCallbackQuery"
    assert params["callback_query_id"] == "cb1"


def test_api_error_is_raised_with_the_description():
    telegram, _ = make({"sendMessage": {"ok": False, "description": "chat not found"}})
    with pytest.raises(TelegramError, match="chat not found"):
        telegram.notify("알림")
