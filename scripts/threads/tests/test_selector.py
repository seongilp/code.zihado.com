import random

import pytest

from poster.selector import NoProjectsError, UnknownSlugError, choose, flatten_projects


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
