"""Run Home Assistant Core fixture tests for this custom integration."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess  # nosec B404
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CORE_PATH = REPO_ROOT.parent / "home-assistant-core-2026.5.1"
DOMAIN = "muller_intuitiv"


def replace_symlink(link: Path, target: Path) -> None:
    """Create or replace a symlink."""
    if link.is_symlink() or link.exists():
        if link.is_dir() and not link.is_symlink():
            shutil.rmtree(link)
        else:
            link.unlink()
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(target)


def main() -> int:
    """Set up a Core checkout test layout and run pytest."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--core-path",
        type=Path,
        default=Path(os.environ.get("HA_CORE_PATH", DEFAULT_CORE_PATH)),
        help="Path to a Home Assistant Core checkout matching the target version.",
    )
    parser.add_argument(
        "pytest_args",
        nargs=argparse.REMAINDER,
        help="Extra pytest arguments after '--'.",
    )
    args = parser.parse_args()

    core_path = args.core_path.resolve()
    if not (core_path / "homeassistant").is_dir() or not (core_path / "tests").is_dir():
        raise SystemExit(f"Home Assistant Core checkout not found: {core_path}")

    replace_symlink(
        core_path / "custom_components" / DOMAIN,
        REPO_ROOT / "custom_components" / DOMAIN,
    )
    replace_symlink(
        core_path / "tests" / "components" / DOMAIN,
        REPO_ROOT / "tests" / "components" / DOMAIN,
    )

    pytest_args = args.pytest_args
    if pytest_args and pytest_args[0] == "--":
        pytest_args = pytest_args[1:]
    if not pytest_args:
        pytest_args = [f"tests/components/{DOMAIN}"]

    return subprocess.run(  # nosec B603
        [sys.executable, "-m", "pytest", *pytest_args],
        cwd=core_path,
        check=False,
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())
