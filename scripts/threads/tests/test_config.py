import pytest

from poster.config import MissingCredentialError, load_dotenv, load_telegram_credentials


def test_load_dotenv_parses_simple_pairs(tmp_path):
    env = tmp_path / ".env"
    env.write_text("A=1\nB=two\n", encoding="utf-8")
    assert load_dotenv(env) == {"A": "1", "B": "two"}


def test_load_dotenv_ignores_comments_and_blank_lines(tmp_path):
    env = tmp_path / ".env"
    env.write_text("# 주석\n\nA=1\n  # 들여쓴 주석\n", encoding="utf-8")
    assert load_dotenv(env) == {"A": "1"}


def test_load_dotenv_strips_export_prefix_and_quotes(tmp_path):
    env = tmp_path / ".env"
    env.write_text('export A="quoted"\nB=\'single\'\n', encoding="utf-8")
    assert load_dotenv(env) == {"A": "quoted", "B": "single"}


def test_load_dotenv_keeps_equals_inside_the_value(tmp_path):
    env = tmp_path / ".env"
    env.write_text("TOKEN=abc=def==\n", encoding="utf-8")
    assert load_dotenv(env) == {"TOKEN": "abc=def=="}


def test_load_dotenv_returns_empty_when_file_is_missing(tmp_path):
    assert load_dotenv(tmp_path / "nope.env") == {}


def test_load_telegram_credentials_reads_both_values(tmp_path):
    env = tmp_path / ".env"
    env.write_text(
        "TELEGRAM_BOT_TOKEN=bot-token\nAUTHORIZED_CHAT_ID=12345\n", encoding="utf-8"
    )
    assert load_telegram_credentials(env) == ("bot-token", "12345")


def test_load_telegram_credentials_raises_when_token_is_absent(tmp_path):
    env = tmp_path / ".env"
    env.write_text("AUTHORIZED_CHAT_ID=12345\n", encoding="utf-8")
    with pytest.raises(MissingCredentialError):
        load_telegram_credentials(env)


def test_load_telegram_credentials_raises_when_chat_id_is_absent(tmp_path):
    env = tmp_path / ".env"
    env.write_text("TELEGRAM_BOT_TOKEN=bot-token\n", encoding="utf-8")
    with pytest.raises(MissingCredentialError):
        load_telegram_credentials(env)
