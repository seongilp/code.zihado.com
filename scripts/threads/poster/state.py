"""상태 파일에 닿는 유일한 경로. 잠금도 여기서만 건다."""

from __future__ import annotations

import fcntl
import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


class LockBusy(RuntimeError):
    """다른 인스턴스가 이미 상태 디렉토리를 잠갔다."""


class State:
    def __init__(self, state_dir: Path | str) -> None:
        self.dir = Path(state_dir)
        self.dir.mkdir(parents=True, exist_ok=True, mode=0o700)

    def path(self, name: str) -> Path:
        return self.dir / name

    def read_json(self, name: str, default: Any) -> Any:
        target = self.path(name)
        if not target.exists():
            return default
        with target.open(encoding="utf-8") as handle:
            return json.load(handle)

    def write_json(self, name: str, value: Any, *, private: bool = False) -> None:
        """임시 파일에 쓰고 rename 한다. 중간에 죽어도 반쪽짜리 파일이 남지 않는다."""
        target = self.path(name)
        fd, tmp_name = tempfile.mkstemp(dir=self.dir, prefix=f".{name}.", suffix=".tmp")
        tmp = Path(tmp_name)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(value, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(tmp, 0o600 if private else 0o644)
            os.replace(tmp, target)
            # rename 자체는 디렉토리 메타데이터 변경이라 따로 sync 해야 살아남는다.
            # 이게 없으면 게시 직후 전원이 나갔을 때 posted.json 이 옛 내용으로
            # 돌아가고, 다음 날 같은 글이 두 번 올라간다.
            dir_fd = os.open(self.dir, os.O_RDONLY)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
        except BaseException:
            tmp.unlink(missing_ok=True)
            raise

    def delete(self, name: str) -> None:
        self.path(name).unlink(missing_ok=True)


@contextmanager
def exclusive_lock(state_dir: Path | str) -> Iterator[None]:
    """겹쳐 실행되면 두 번째는 LockBusy 로 즉시 빠져나간다.

    재진입 불가 — 같은 프로세스에서 두 번 잡아도 LockBusy 가 난다.
    진입점에서 딱 한 번만 잡을 것.
    """
    directory = Path(state_dir)
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = os.open(directory / "lock", os.O_CREAT | os.O_RDWR, 0o600)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise LockBusy("다른 인스턴스가 실행 중입니다") from exc
        yield
    finally:
        os.close(fd)
