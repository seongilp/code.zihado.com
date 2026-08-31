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
    python3 scripts/scan-dirs.py --all       # 스캔된 전체 목록
    python3 scripts/scan-dirs.py --new-only  # 새 후보 키만 한 줄씩 (자동화 점검용)
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
    # (web/, temp/, study/, app_in_toss/ 처럼 통째로 제외하기로 한 폴더의 내부를
    #  매번 다시 물어보면 진짜 누락이 잡음에 묻힌다.)
    #
    # !!! 두 종류의 컨테이너를 절대 헷갈리지 마라 — 이 실명은 두 번 났다 !!!
    #   - datalab 처럼 "쇼케이스할 앱들을 담는" 컨테이너: 부모 자신은 카드가
    #     아니지만 하위는 반드시 스캔 후보여야 한다 → status="container".
    #   - temp/study 처럼 "통째로 무시하는" 컨테이너 → status="skipped"/"excluded".
    #
    # 처음엔 datalab 하위 4개가 컨테이너 목록을 손으로 유지하다 몇 주간 누락됐고,
    # 그걸 이 스캐너로 고쳤다. 그런데 datalab 을 skipped 로 표시하는 순간 하위가
    # 이 blocked 규칙에 걸려 같은 실명이 되살아났다(두 번째 발생). 그래서 "무시"와
    # "컨테이너"를 status 로 명확히 갈랐다. container 는 절대 blocked 에 넣지 않는다.
    # 다음 사람에게: datalab 을 skipped 로 되돌리지 마라. 하위 앱이 조용히 사라진다.
    blocked = {
        k for k, v in directories.items()
        if "/" not in k and v.get("status") in ("skipped", "excluded")
    }

    # 재발 방지 가드: skipped/excluded 로 막아둔 부모인데 하위 카드가 index 에
    # 남아 있으면 모순이다 — 누군가 container 를 다시 skipped 로 되돌렸다는 뜻이고,
    # 그 순간 하위가 스캔에서 통째로 사라진다. 사후 감시(--new-only)가 감시 대상과
    # 똑같은 blocked 규칙을 타기 때문에, 이 모순만은 규칙 바깥에서 직접 잡아낸다.
    # (감시 장치가 감시 대상과 같은 결함을 공유하면 감시가 아니다.)
    mislabeled = sorted(
        p for p in blocked
        if any(k.startswith(p + "/") for k in directories)
    )

    def is_blocked(key):
        return "/" in key and key.split("/", 1)[0] in blocked

    new = [k for k in keys if k not in directories and not is_blocked(k)]

    # scan 이 하위를 내보낸 부모(datalab, macos, cli, native ...)의 bare 키는
    # "사라진 항목"이 아니다 — 카드를 하위 키로 추적할 뿐 부모는 원래 카드가 아니다.
    # 그걸 gone 에 남기면 진짜 삭제된 프로젝트가 잡음에 묻힌다.
    emitted_parents = {k.split("/", 1)[0] for k in keys if "/" in k}
    gone = [k for k in directories if k not in keys and k not in emitted_parents]

    # 자동화가 "정말 남은 게 없나"를 기계적으로 확인할 때 쓰는 모드.
    # 갱신 에이전트가 "변경 없음"이라고 보고해도, 여기서 후보가 나오면 놓친 것이다.
    # 컨테이너 오분류도 여기에 한 줄로 섞어 내보낸다 — auto-update.sh 의 가드가
    # 이 출력이 비어있지 않으면 알림을 보내므로, 재발이 즉시 사람에게 도달한다.
    if "--new-only" in sys.argv:
        out = list(new)
        for p in mislabeled:
            n = sum(1 for k in directories if k.startswith(p + "/"))
            out.append(
                "!! 컨테이너 오분류: '%s' 가 skipped/excluded 인데 하위 카드 %d개가 "
                "index 에 있음 — status 를 'container' 로 되돌려야 하위 스캔이 살아난다"
                % (p, n)
            )
        print("\n".join(out))
        return

    # 오분류는 조용히 지나가면 안 되는 재발 신호다. 맨 위에 눈에 띄게 경고한다.
    if mislabeled:
        for p in mislabeled:
            n = sum(1 for k in directories if k.startswith(p + "/"))
            print(
                "!! 컨테이너 오분류: '%s' 가 skipped/excluded 인데 하위 카드 %d개가 "
                "index 에 있음 — status 를 'container' 로 고쳐라 (하위가 스캔에서 사라진다)"
                % (p, n),
                file=sys.stderr,
            )

    print("# 새 후보 (index 에 없는 프로젝트 디렉토리) — %d개" % len(new))
    for k in new:
        print(k)
    print()
    print("# 사라진 항목 (index 에는 있으나 디렉토리가 없음) — %d개" % len(gone))
    for k in gone:
        print("%s  [%s]" % (k, directories[k].get("status", "?")))


if __name__ == "__main__":
    main()
