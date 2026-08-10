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


def test_clean_keeps_quotes_when_the_whole_string_is_not_one_quoted_span():
    assert clean('"안녕" 그리고 "잘가"') == '"안녕" 그리고 "잘가"'


def test_clean_keeps_curly_quotes_when_not_one_quoted_span():
    assert clean("“안녕” 그리고 “잘가”") == "“안녕” 그리고 “잘가”"


def test_clean_removes_a_single_line_fence():
    assert clean("```본문```") == "본문"


def test_clean_removes_a_fence_tagged_with_digits():
    assert clean("```py3\n본문\n```") == "본문"


def test_clean_unwraps_a_fence_nested_inside_quotes():
    assert clean('"```\n본문\n```"') == "본문"


def test_clean_leaves_doubled_quotes_alone():
    # 안쪽에 따옴표가 남아 있으면 벗기지 않는다. '"안녕" 그리고 "잘가"' 를
    # 지키려면 이 경우도 포기해야 한다 — 둘을 구분할 방법이 없다.
    # 따옴표가 남는 쪽이 본문이 망가지는 쪽보다 낫다.
    assert clean('""본문""') == '""본문""'


def test_clean_normalises_crlf():
    assert clean("```\r\n본문\r\n```") == "본문"


def test_clean_can_return_empty_for_an_empty_fence():
    assert clean("```\n\n```") == ""


def test_validate_rejects_whitespace_only_text():
    with pytest.raises(EmptyTextError):
        validate("   ")
