"""오늘 소개할 프로젝트를 고른다. 파일 I/O 도 네트워크도 모른다."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, Sequence


class NoProjectsError(RuntimeError):
    """projects.json 에 프로젝트가 하나도 없다."""


class UnknownSlugError(RuntimeError):
    """--project 로 지정한 slug 가 카탈로그에 없다."""


@dataclass(frozen=True)
class Selection:
    project: dict[str, Any]
    round: int
    previous_texts: tuple[str, ...]


def flatten_projects(catalog: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        project
        for category in catalog.get("categories", [])
        for project in category.get("projects", [])
    ]


def _previous_texts(posted: Sequence[dict], slug: str) -> tuple[str, ...]:
    return tuple(
        record["text"]
        for record in posted
        if record.get("slug") == slug and record.get("text")
    )


def _next_round_for(posted: Sequence[dict], slug: str) -> int:
    rounds = [r.get("round", 1) for r in posted if r.get("slug") == slug]
    return max(rounds) + 1 if rounds else 1


def choose(
    catalog: dict[str, Any],
    posted: Sequence[dict],
    *,
    rng: random.Random,
    force_slug: str | None = None,
) -> Selection:
    projects = flatten_projects(catalog)
    if not projects:
        raise NoProjectsError("projects.json 에 프로젝트가 없습니다")

    if force_slug is not None:
        project = next((p for p in projects if p.get("slug") == force_slug), None)
        if project is None:
            raise UnknownSlugError(f"알 수 없는 slug: {force_slug}")
        return Selection(
            project=project,
            round=_next_round_for(posted, force_slug),
            previous_texts=_previous_texts(posted, force_slug),
        )

    # 이번 회차에서 아직 안 다룬 프로젝트가 없으면 다음 회차를 연다.
    current = 1
    while True:
        done = {r.get("slug") for r in posted if r.get("round", 1) == current}
        candidates = [p for p in projects if p.get("slug") not in done]
        if candidates:
            break
        current += 1

    # 정렬해서 넘겨야 같은 시드로 같은 결과가 나온다.
    project = rng.choice(sorted(candidates, key=lambda p: p["slug"]))
    return Selection(
        project=project,
        round=current,
        previous_texts=_previous_texts(posted, project["slug"]),
    )
