import json
import os

import pytest

from poster.state import LockBusy, State, exclusive_lock


def test_read_json_returns_default_when_missing(tmp_path):
    state = State(tmp_path)
    assert state.read_json("posted.json", []) == []


def test_write_then_read_roundtrip_keeps_korean(tmp_path):
    state = State(tmp_path)
    state.write_json("posted.json", [{"slug": "law", "text": "한글"}])
    assert state.read_json("posted.json", []) == [{"slug": "law", "text": "한글"}]


def test_write_json_is_atomic_and_leaves_no_temp_files(tmp_path):
    state = State(tmp_path)
    state.write_json("posted.json", [{"slug": "law"}])
    leftovers = [p.name for p in tmp_path.iterdir() if p.name.startswith(".")]
    assert leftovers == []


def test_write_json_private_sets_owner_only_permissions(tmp_path):
    state = State(tmp_path)
    state.write_json("token.json", {"token": "secret"}, private=True)
    mode = os.stat(tmp_path / "token.json").st_mode & 0o777
    assert mode == 0o600


def test_delete_is_idempotent(tmp_path):
    state = State(tmp_path)
    state.delete("pending.json")  # 없어도 예외가 나지 않는다
    state.write_json("pending.json", {"slug": "law"})
    state.delete("pending.json")
    assert not (tmp_path / "pending.json").exists()


def test_second_lock_raises_lock_busy(tmp_path):
    with exclusive_lock(tmp_path):
        with pytest.raises(LockBusy):
            with exclusive_lock(tmp_path):
                pass


def test_lock_is_released_after_exit(tmp_path):
    with exclusive_lock(tmp_path):
        pass
    with exclusive_lock(tmp_path):
        pass  # 예외 없이 다시 잡힌다


def test_failed_write_leaves_previous_file_intact(tmp_path):
    state = State(tmp_path)
    state.write_json("posted.json", [{"slug": "law"}])
    with pytest.raises(TypeError):
        state.write_json("posted.json", {"bad": {1, 2}})  # set → 직렬화 도중 실패
    assert state.read_json("posted.json", None) == [{"slug": "law"}]
    assert [p.name for p in tmp_path.iterdir()] == ["posted.json"]
