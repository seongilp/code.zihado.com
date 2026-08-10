"""오늘 소개할 프로젝트를 고른다. 파일 I/O 도 네트워크도 모른다."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, Sequence


class NoProjectsError(RuntimeError):
    """projects.json 에 프로젝트가 하나도 없다."""


class UnknownSlugError(RuntimeError):
    """--project 로 지정한 slug 가 카탈로그에 없다."""


class MalformedCatalogError(RuntimeError):
    """projects.json 의 항목에 slug 가 없다. 어느 분류인지 알려 준다."""


@dataclass(frozen=True)
class Selection:
    project: dict[str, Any]
    round: int
    previous_texts: tuple[str, ...]


def flatten_projects(catalog: dict[str, Any]) -> list[dict[str, Any]]:
    projects: list[dict[str, Any]] = []
    for category in catalog.get("categories", []):
        for project in category.get("projects", []):
            if not project.get("slug"):
                # projects.json 은 손으로 관리한다. 어느 분류에서 깨졌는지
                # 말해 주지 않으면 60개를 눈으로 뒤져야 한다.
                raise MalformedCatalogError(
                    f"slug 없는 항목이 있습니다 — 분류 '{category.get('id', '?')}', "
                    f"이름 '{project.get('name', '?')}'"
                )
            projects.append(project)
    return projects


def _round_of(record: dict) -> int:
    """손으로 고친 posted.json 의 round 가 깨져 있어도 버티게 한다.

    회차를 못 읽어 기록이 안 보이면 그 프로젝트는 '한 번도 안 올린 것'이 되어
    같은 글이 두 번 올라간다. 조용한 중복 게시보다 1회차로 뭉개는 편이 낫다.
    """
    try:
        value = int(record.get("round", 1))
    except (TypeError, ValueError):
        return 1
    return value if value >= 1 else 1


def _previous_texts(posted: Sequence[dict], slug: str) -> tuple[str, ...]:
    return tuple(
        record["text"]
        for record in posted
        if record.get("slug") == slug and record.get("text")
    )


def _next_round_for(posted: Sequence[dict], slug: str) -> int:
    """--project 로 지정하면 그 프로젝트의 마지막 회차 다음으로 올린다.

    1회차가 아직 진행 중이어도 이미 올린 프로젝트라면 2회차가 된다.
    같은 회차에 같은 글이 두 번 들어가지 않게 하려면 이 규칙뿐이다.
    """
    rounds = [_round_of(r) for r in posted if r.get("slug") == slug]
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
        done = {r.get("slug") for r in posted if _round_of(r) == current}
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
