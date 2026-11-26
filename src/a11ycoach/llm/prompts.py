"""Load and manage versioned prompt files."""

import re
from pathlib import Path

_VERSION = re.compile(r"_v(\d+)$")


def read_prompt(directory: Path, name: str) -> str:
    return (directory / f"{name}.md").read_text(encoding="utf-8").strip()


def versions(directory: Path, task: str) -> list[str]:
    names = [p.stem for p in directory.glob(f"{task}_v*.md") if _VERSION.search(p.stem)]
    return sorted(names, key=lambda name: int(_VERSION.search(name).group(1)))


def latest(directory: Path, task: str) -> str:
    found = versions(directory, task)
    if not found:
        raise FileNotFoundError(f"no prompt file {directory}/{task}_v1.md")
    return found[-1]
