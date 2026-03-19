from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def has_module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def run_step(title: str, command: list[str], cwd: Path) -> None:
    print(f"[verify] {title}")
    subprocess.run(command, cwd=cwd, check=True)


def main() -> int:
    steps: list[tuple[str, list[str], Path]] = [
        (
            "backend compile",
            [sys.executable, "-m", "py_compile", "backend/__init__.py", "backend/main.py", "backend/app/factory.py", "backend/app/bindings.py", "backend/data/models.py", "backend/data/mongo_repository.py", "backend/routing/router.py", "backend/routing/routing.py", "backend/routing/object_id.py", "backend/routing/error_mapper.py"],
            ROOT,
        ),
        (
            "data_handler tests",
            [sys.executable, "-m", "unittest", "discover", "-s", "data_handler/tests", "-p", "test_*.py"],
            ROOT,
        ),
        (
            "legacy runtime tests",
            [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"],
            ROOT / "witterungsstation_py",
        ),
        (
            "frontend tests",
            ["npm", "run", "test:run"],
            ROOT / "frontend",
        ),
        (
            "frontend build",
            ["npm", "run", "build"],
            ROOT / "frontend",
        ),
    ]

    try:
        for title, command, cwd in steps:
            run_step(title, command, cwd)

        if has_module("fastapi") and has_module("pydantic"):
            run_step(
                "backend helper tests",
                [sys.executable, "-m", "unittest", "discover", "-s", "backend/tests", "-p", "test_*.py"],
                ROOT,
            )
            run_step(
                "backend app import",
                [sys.executable, "-c", "from backend.main import app; print(len(app.router.routes))"],
                ROOT,
            )
        else:
            print("[verify] backend app import skipped (missing fastapi/pydantic in current interpreter)")
    except subprocess.CalledProcessError as exc:
        print(f"[verify] failed: {exc}")
        return int(exc.returncode or 1)

    print("[verify] all checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
