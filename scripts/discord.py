#!/usr/bin/env python3
"""Discord 웹훅 알림 — 포트폴리오 목록 게시 / 한 줄 메시지 전송.

웹훅 URL 은 공개 저장소에 들어가면 안 되므로 절대 하드코딩하지 않고
환경변수 DISCORD_WEBHOOK_PORTFOLIO (없으면 ~/.env) 에서만 읽는다.

사용법:
    python3 scripts/discord.py --list            # projects.json 전체 목록 게시
    python3 scripts/discord.py --message "텍스트"  # 한 줄 알림
"""
from __future__ import annotations

import argparse
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PROJECTS_JSON = REPO / "projects.json"
ENV_FILE = Path.home() / ".env"
ENV_KEY = "DISCORD_WEBHOOK_PORTFOLIO"

# Discord 하드 리밋 — 넘기면 400 이 떨어진다
MAX_CONTENT = 2000
MAX_EMBED_DESC = 4096
MAX_EMBEDS_PER_MESSAGE = 10
# 한 메시지에 담긴 모든 임베드의 글자 수 합계 상한
MAX_EMBED_CHARS_PER_MESSAGE = 6000

EMBED_COLOR = 0x5865F2

# Discord 앞단의 Cloudflare 는 기본 urllib User-Agent 를 1010 으로 막는다.
USER_AGENT = "code-zihado-portfolio/1.0 (+https://code.zihado.com)"


class DiscordError(RuntimeError):
    pass


def ssl_context() -> ssl.SSLContext:
    """launchd 로 도는 파이썬은 시스템 루트 인증서를 못 찾는 경우가 있어 certifi 를 쓴다."""
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def read_webhook() -> str:
    """환경변수 우선, 없으면 ~/.env 에서 읽는다."""
    url = os.environ.get(ENV_KEY, "").strip()
    if not url and ENV_FILE.is_file():
        for raw in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line.startswith(f"{ENV_KEY}="):
                continue
            url = line.split("=", 1)[1].strip().strip("'\"")
            break
    if not url.startswith("https://discord.com/api/webhooks/"):
        raise DiscordError(
            f"{ENV_KEY} 가 없거나 Discord 웹훅 URL 이 아닙니다. ~/.env 에 넣어 주세요."
        )
    return url


def post(webhook: str, payload: dict, *, retries: int = 3) -> None:
    """웹훅으로 한 건 전송. 429(레이트리밋)는 Retry-After 만큼 기다렸다 재시도."""
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    for attempt in range(1, retries + 1):
        req = urllib.request.Request(
            webhook,
            data=body,
            headers={"Content-Type": "application/json", "User-Agent": USER_AGENT},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=20, context=ssl_context()):
                return
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:400]
            if exc.code == 429 and attempt < retries:
                wait = 5.0
                try:
                    wait = float(json.loads(detail).get("retry_after", wait))
                except (ValueError, TypeError):
                    pass
                time.sleep(min(wait, 30.0))
                continue
            raise DiscordError(f"Discord 전송 실패 (HTTP {exc.code}): {detail}") from exc
        except urllib.error.URLError as exc:
            if attempt < retries:
                time.sleep(2.0 * attempt)
                continue
            raise DiscordError(f"Discord 연결 실패: {exc.reason}") from exc


def send_message(webhook: str, text: str) -> None:
    """긴 텍스트는 2000자 단위로 잘라 여러 건으로 보낸다."""
    for chunk in split_text(text, MAX_CONTENT):
        post(webhook, {"content": chunk})


def split_text(text: str, limit: int) -> list[str]:
    """줄 단위로 limit 이하 덩어리로 쪼갠다. 한 줄이 limit 을 넘으면 그 줄만 강제로 자른다."""
    chunks: list[str] = []
    current = ""
    for line in text.split("\n"):
        while len(line) > limit:
            if current:
                chunks.append(current)
                current = ""
            chunks.append(line[:limit])
            line = line[limit:]
        candidate = f"{current}\n{line}" if current else line
        if len(candidate) > limit:
            chunks.append(current)
            current = line
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


SITE = "https://code.zihado.com"


def landing_url(project: dict) -> str:
    """포트폴리오 사이트의 해당 카드 딥링크 (index.html 의 #p/<slug> 라우팅)."""
    slug = project.get("slug", "").strip()
    return f"{SITE}/#p/{slug}" if slug else ""


def repo_label(url: str) -> str:
    """저장소 호스트에 맞는 라벨 — 전부 GitHub 인 건 아니다 (codeberg 등)."""
    host = urllib.parse.urlparse(url).hostname or ""
    host = host[4:] if host.startswith("www.") else host
    return "GitHub" if host == "github.com" else host


def project_line(project: dict) -> str:
    """프로젝트 한 건 — 이름/한 줄 소개 + 저장소 · 랜딩 · 접속 주소 세 링크.

    저장소 링크가 없는 프로젝트는 비공개 저장소라는 뜻이라 (미공개)로 표시한다.
    """
    name = project.get("name", project.get("slug", "이름 없음"))
    one_liner = (project.get("oneLiner") or "").strip()

    repo = project.get("github") or ""
    live = project.get("live") or ""

    parts = [
        f"[{repo_label(repo)}]({repo})" if repo else "🔒 private (미공개)",
        f"[랜딩]({landing_url(project)})",
        f"[접속]({live})" if live else "접속 (없음)",
    ]

    head = f"**{name}**"
    if one_liner:
        head += f" — {one_liner}"
    return f"• {head}\n  {' · '.join(parts)}"


def category_embeds(category: dict) -> list[dict]:
    """한 분야를 임베드로. 설명이 4096자를 넘으면 (1/2) 식으로 나눈다."""
    emoji = category.get("emoji", "")
    title = f"{emoji} {category.get('name', category.get('id', ''))}".strip()
    projects = category.get("projects", [])
    lines = [project_line(p) for p in projects]
    parts = split_text("\n".join(lines), MAX_EMBED_DESC)
    total = len(parts)
    return [
        {
            "title": title if total == 1 else f"{title} ({i}/{total})",
            "description": part,
            "color": EMBED_COLOR,
            **({"footer": {"text": f"{len(projects)}개"}} if i == total else {}),
        }
        for i, part in enumerate(parts, start=1)
    ]


def post_list(webhook: str) -> int:
    data = json.loads(PROJECTS_JSON.read_text(encoding="utf-8"))
    meta = data.get("meta", {})
    categories = data.get("categories", [])
    total = sum(len(c.get("projects", [])) for c in categories)
    goal = meta.get("goal", {})
    target = goal.get("target")

    header = f"## 📚 {meta.get('title', '포트폴리오')}\n"
    if target:
        header += f"지금까지 **{total}개** / 목표 {target}개 — 남은 건 {max(target - total, 0)}개\n"
    else:
        header += f"총 **{total}개**\n"
    header += f"기준일 {meta.get('generatedAt', '-')} · https://code.zihado.com"
    send_message(webhook, header)

    embeds: list[dict] = []
    for category in categories:
        embeds.extend(category_embeds(category))
    for batch in batch_embeds(embeds):
        post(webhook, {"embeds": batch})
    return total


def embed_size(embed: dict) -> int:
    return (
        len(embed.get("title", ""))
        + len(embed.get("description", ""))
        + len(embed.get("footer", {}).get("text", ""))
    )


def batch_embeds(embeds: list[dict]) -> list[list[dict]]:
    """개수(10)와 글자 수 합계(6000) 상한을 둘 다 지키도록 임베드를 묶는다."""
    batches: list[list[dict]] = []
    current: list[dict] = []
    size = 0
    for embed in embeds:
        this = embed_size(embed)
        if current and (
            len(current) >= MAX_EMBEDS_PER_MESSAGE
            or size + this > MAX_EMBED_CHARS_PER_MESSAGE
        ):
            batches.append(current)
            current, size = [], 0
        current.append(embed)
        size += this
    if current:
        batches.append(current)
    return batches


def main() -> int:
    parser = argparse.ArgumentParser(description="포트폴리오 Discord 알림")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--list", action="store_true", help="projects.json 전체 목록을 게시")
    group.add_argument("--message", help="한 줄 알림 전송")
    args = parser.parse_args()

    try:
        webhook = read_webhook()
        if args.list:
            count = post_list(webhook)
            print(f"OK: 포트폴리오 {count}개를 Discord 에 게시했습니다.")
        else:
            send_message(webhook, args.message)
            print("OK: Discord 알림 전송 완료.")
    except (DiscordError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
