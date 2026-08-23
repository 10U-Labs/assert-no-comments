"""Unit test configuration."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def tiny_tree(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Build a three-file tree and enter it, because every path here is relative.

    Returns:
        The tree root, holding one clean file and two commented ones.
    """
    kept = tmp_path / "kept"
    kept.mkdir()
    (kept / "clean.py").write_text("x = 1\n", encoding="utf-8")
    (kept / "first.py").write_text("x = 1\n# why\n", encoding="utf-8")
    (kept / "second.py").write_text("# why\ny = 2\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    return tmp_path
