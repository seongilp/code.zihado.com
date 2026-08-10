import random

import pytest

from poster.selector import (
    MalformedCatalogError,
    NoProjectsError,
    UnknownSlugError,
    choose,
    flatten_projects,
)


def catalog(*slugs):
    return {
        "categories": [
            {"id": "web", "projects": [{"slug": s, "name": s.upper()} for s in slugs]}
        ]
    }


def rng():
    return random.Random(42)


def test_flatten_projects_walks_every_category():
    data = {
        "categories": [
            {"id": "web", "projects": [{"slug": "a"}]},
            {"id": "cli", "projects": [{"slug": "b"}, {"slug": "c"}]},
        ]
    }
    assert [p["slug"] for p in flatten_projects(data)] == ["a", "b", "c"]


def test_choose_picks_from_projects_when_nothing_posted():
    selection = choose(catalog("a", "b"), [], rng=rng())
    assert selection.project["slug"] in {"a", "b"}
    assert selection.round == 1
    assert selection.previous_texts == ()


def test_choose_never_repeats_within_a_round():
    posted = [{"slug": "a", "round": 1}]
    selection = choose(catalog("a", "b"), posted, rng=rng())
    assert selection.project["slug"] == "b"


def test_skipped_projects_are_not_offered_again_in_the_same_round():
    posted = [{"slug": "a", "round": 1, "skipped": True}]
    selection = choose(catalog("a", "b"), posted, rng=rng())
    assert selection.project["slug"] == "b"


def test_round_advances_when_every_project_is_covered():
    posted = [{"slug": "a", "round": 1}, {"slug": "b", "round": 1}]
    selection = choose(catalog("a", "b"), posted, rng=rng())
    assert selection.round == 2


def test_second_round_carries_previous_texts_for_that_project():
    posted = [
        {"slug": "a", "round": 1, "text": "1회차 본문"},
        {"slug": "b", "round": 1, "text": "다른 프로젝트"},
    ]
    selection = choose(catalog("a"), posted, rng=rng())
    assert selection.round == 2
    assert selection.previous_texts == ("1회차 본문",)


def test_skipped_records_contribute_no_previous_text():
    posted = [{"slug": "a", "round": 1, "skipped": True}]
    selection = choose(catalog("a"), posted, rng=rng())
    assert selection.previous_texts == ()


def test_force_slug_selects_that_project_at_its_next_round():
    posted = [{"slug": "a", "round": 1, "text": "예전 글"}]
    selection = choose(catalog("a", "b"), posted, rng=rng(), force_slug="a")
    assert selection.project["slug"] == "a"
    assert selection.round == 2
    assert selection.previous_texts == ("예전 글",)


def test_force_slug_rejects_unknown_slug():
    with pytest.raises(UnknownSlugError):
        choose(catalog("a"), [], rng=rng(), force_slug="nope")


def test_empty_catalog_raises():
    with pytest.raises(NoProjectsError):
        choose({"categories": []}, [], rng=rng())


def test_selection_is_deterministic_for_a_seeded_rng():
    first = choose(catalog("a", "b", "c"), [], rng=random.Random(7))
    second = choose(catalog("a", "b", "c"), [], rng=random.Random(7))
    assert first.project["slug"] == second.project["slug"]


def test_string_round_is_treated_as_a_number_not_ignored():
    # posted.json 을 손으로 고쳐 round 가 문자열이 되어도 기록이 사라지면 안 된다.
    # 사라지면 그 프로젝트를 안 올린 것으로 보고 같은 글을 두 번 올린다.
    posted = [{"slug": "a", "round": "1"}]
    selection = choose(catalog("a", "b"), posted, rng=rng())
    assert selection.project["slug"] == "b"


def test_garbage_round_falls_back_to_round_one():
    posted = [{"slug": "a", "round": "어제"}]
    selection = choose(catalog("a", "b"), posted, rng=rng())
    assert selection.project["slug"] == "b"


def test_zero_or_negative_round_falls_back_to_round_one():
    posted = [{"slug": "a", "round": 0}, {"slug": "b", "round": -3}]
    selection = choose(catalog("a", "b"), posted, rng=rng())
    assert selection.round == 2


def test_string_round_does_not_crash_force_slug():
    posted = [{"slug": "a", "round": "2"}]
    selection = choose(catalog("a"), posted, rng=rng(), force_slug="a")
    assert selection.round == 3


def test_project_without_slug_names_its_category():
    broken = {"categories": [{"id": "web", "projects": [{"name": "이름만 있음"}]}]}
    with pytest.raises(MalformedCatalogError, match="web"):
        flatten_projects(broken)


def test_round_two_excludes_projects_already_posted_in_round_two():
    posted = [
        {"slug": "a", "round": 1},
        {"slug": "b", "round": 1},
        {"slug": "a", "round": 2},
    ]
    selection = choose(catalog("a", "b"), posted, rng=rng())
    assert selection.project["slug"] == "b"
    assert selection.round == 2
