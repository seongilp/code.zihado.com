import pytest

from poster.sanitize import MAX_LENGTH, EmptyTextError, TooLongError, clean, validate


def test_clean_strips_surrounding_whitespace():
    assert clean("\n  본문  \n") == "본문"


def test_clean_removes_plain_code_fence():
    assert clean("```\n본문\n```") == "본문"


def test_clean_removes_language_tagged_code_fence():
    assert clean("```text\n본문\n```") == "본문"


def test_clean_removes_wrapping_straight_quotes():
    assert clean('"본문"') == "본문"


def test_clean_removes_wrapping_curly_quotes():
    assert clean("“본문”") == "본문"


def test_clean_keeps_inner_quotes():
    assert clean('그는 "안녕"이라고 했다') == '그는 "안녕"이라고 했다'


def test_clean_collapses_three_or_more_blank_lines():
    assert clean("가\n\n\n\n나") == "가\n\n나"


def test_clean_keeps_a_single_blank_line():
    assert clean("가\n\n나") == "가\n\n나"


def test_validate_returns_text_at_the_limit():
    text = "가" * MAX_LENGTH
    assert validate(text) == text


def test_validate_rejects_one_over_the_limit():
    with pytest.raises(TooLongError) as excinfo:
        validate("가" * (MAX_LENGTH + 1))
    assert excinfo.value.length == MAX_LENGTH + 1


def test_validate_rejects_empty_text():
    with pytest.raises(EmptyTextError):
        validate("")


def test_too_long_error_keeps_the_text_for_the_warning_path():
    text = "가" * (MAX_LENGTH + 5)
    with pytest.raises(TooLongError) as excinfo:
        validate(text)
    assert excinfo.value.text == text
