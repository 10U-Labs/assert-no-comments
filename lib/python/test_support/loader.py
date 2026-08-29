from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


def read_sample(directory: Path, name: str) -> str:
    return (directory / "samples" / f"{name}.txt").read_text(encoding="utf-8")
