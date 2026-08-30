#!/usr/bin/env python3
"""~/work/playground 를 훑어 아직 쇼케이스에 없는 프로젝트 디렉토리를 찾는다.

왜 이 스크립트가 있나:
    예전에는 컨테이너 디렉토리 목록(macos, native, vms)이 update-prompt.md 안에
    손으로 적혀 있었다. datalab/ 처럼 새 컨테이너가 생기면 그 안의 프로젝트가 통째로
    스캔에서 빠지는데, 아무도 실패 신호를 못 받으니 몇 주가 지나도 모른다.
    실제로 datalab 하위 4개가 그렇게 누락됐다. 그래서 목록을 손으로 유지하는 대신
    "무엇이 프로젝트인가"를 규칙으로 판별하고, index 와의 대조까지 여기서 끝낸다.

판별 규칙:
    1) 최상위 디렉토리에 프로젝트 표식(.git / package.json / Package.swift / Cargo.toml /
       pubspec.yaml / pyproject.toml / README.md)이 있으면 그 자체가 프로젝트다.
    2) 없으면 컨테이너로 보고 한 단계만 내려가 같은 기준을 만족하는 하위 디렉토리를
       "부모/자식" 형태로 내보낸다. 두 단계 이상은 내려가지 않는다 — 모노레포 내부까지
       파고들면 카드가 아니라 소스 트리를 나열하게 된다.
    3) 둘 다 아니면(빈 폴더·문서만 있는 폴더) 부모 이름만 내보낸다. 판단은 사람이 하고
       index 에 skipped 로 기록하면 된다.

사용법:
    python3 scripts/scan-dirs.py          # 새 후보 / 사라진 항목만 보고
    python3 scripts/scan-dirs.py --all    # 스캔된 전체 목록
"""
import json
import os
import sys

MARKERS = (
    ".git",
    "package.json",
    "Package.swift",
    "Cargo.toml",
    "pubspec.yaml",
    "pyproject.toml",
    "README.md",
)

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(REPO, "playground-index.json")


def is_project(path):
    return any(os.path.exists(os.path.join(path, m)) for m in MARKERS)


def subdirs(path):
    try:
        names = sorted(os.listdir(path))
    except OSError:
        return []
    return [
        n for n in names
        if not n.startswith(".") and os.path.isdir(os.path.join(path, n))
    ]


def scan(root):
    """프로젝트 디렉토리 키 목록을 돌려준다."""
    keys = []
    for name in subdirs(root):
        path = os.path.join(root, name)
        if is_project(path):
            keys.append(name)
            continue
        children = [c for c in subdirs(path) if is_project(os.path.join(path, c))]
        if children:
            keys.extend("%s/%s" % (name, c) for c in children)
        else:
            keys.append(name)
    return keys


def main():
    root = os.path.expanduser("~/work/playground")
    keys = scan(root)

    if "--all" in sys.argv:
        print("\n".join(keys))
        return

    with open(INDEX, encoding="utf-8") as f:
        directories = json.load(f)["directories"]

    # 부모가 skipped/excluded 면 그 안의 하위 디렉토리도 조사 대상이 아니다.
    # (web/, temp/, study/ 처럼 통째로 제외하기로 한 폴더의 내부를 매번 다시 물어보면
    #  진짜 누락이 잡음에 묻힌다.)
    blocked = {
        k for k, v in directories.items()
        if "/" not in k and v.get("status") in ("skipped", "excluded")
    }

    def is_blocked(key):
        return "/" in key and key.split("/", 1)[0] in blocked

    new = [k for k in keys if k not in directories and not is_blocked(k)]
    gone = [k for k in directories if k not in keys]

    print("# 새 후보 (index 에 없는 프로젝트 디렉토리) — %d개" % len(new))
    for k in new:
        print(k)
    print()
    print("# 사라진 항목 (index 에는 있으나 디렉토리가 없음) — %d개" % len(gone))
    for k in gone:
        print("%s  [%s]" % (k, directories[k].get("status", "?")))


if __name__ == "__main__":
    main()
