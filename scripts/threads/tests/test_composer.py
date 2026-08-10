import pytest

from poster.composer import ComposeFailed, ComposeResult, build_prompt, compose
from poster.selector import Selection


def selection(round_=1, previous=()):
    return Selection(
        project={"slug": "law", "name": "법령 검색", "live": "https://law.zihado.com"},
        round=round_,
        previous_texts=previous,
    )


def test_build_prompt_starts_with_the_instructions():
    prompt = build_prompt("지침 본문", selection())
    assert prompt.startswith("지침 본문")


def test_build_prompt_embeds_the_project_json():
    prompt = build_prompt("지침", selection())
    assert '"slug": "law"' in prompt
    assert "법령 검색" in prompt


def test_build_prompt_omits_previous_texts_on_the_first_round():
    prompt = build_prompt("지침", selection())
    assert "이전 회차" not in prompt


def test_build_prompt_includes_previous_texts_from_the_second_round():
    prompt = build_prompt("지침", selection(round_=2, previous=("예전에 쓴 글",)))
    assert "이전 회차" in prompt
    assert "예전에 쓴 글" in prompt


def test_compose_returns_the_cleaned_text():
    result = compose("지침", selection(), runner=lambda prompt: "```\n  본문  \n```")
    assert result == ComposeResult(text="본문", warning=None)


def test_compose_retries_once_when_the_first_draft_is_too_long():
    drafts = iter(["가" * 600, "짧은 본문"])
    calls = []

    def runner(prompt):
        calls.append(prompt)
        return next(drafts)

    result = compose("지침", selection(), runner=runner)
    assert result.text == "짧은 본문"
    assert result.warning is None
    assert len(calls) == 2


def test_the_retry_prompt_tells_the_model_it_was_too_long():
    drafts = iter(["가" * 600, "짧은 본문"])
    calls = []

    def runner(prompt):
        calls.append(prompt)
        return next(drafts)

    compose("지침", selection(), runner=runner)
    assert "500자" in calls[1]


def test_compose_surrenders_with_a_warning_after_two_long_drafts():
    result = compose("지침", selection(), runner=lambda prompt: "가" * 600)
    assert result.text == "가" * 600
    assert result.warning is not None
    assert "600" in result.warning


def test_compose_raises_when_the_model_returns_nothing():
    with pytest.raises(ComposeFailed):
        compose("지침", selection(), runner=lambda prompt: "   ")


def test_compose_raises_when_the_runner_blows_up():
    def runner(prompt):
        raise OSError("claude 를 찾을 수 없습니다")

    with pytest.raises(ComposeFailed, match="claude"):
        compose("지침", selection(), runner=runner)
