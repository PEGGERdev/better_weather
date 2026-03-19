from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
DATA_HANDLER_ENTRY = ROOT / "data_handler_service.py"
DIRECT_WEATHER_TEST = ROOT / "testbench" / "run_direct_weather_station_test.py"
BACKEND_PY = BACKEND_DIR / ".venv" / "bin" / "python"
DH_PY = ROOT / "witterungsstation_py" / ".venv" / "bin" / "python"


def _http_json(url: str):
    with urllib.request.urlopen(url, timeout=5) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _is_backend_up() -> bool:
    try:
        _http_json("http://127.0.0.1:8000/weather/")
        return True
    except Exception:
        return False


def _start_backend_if_needed() -> subprocess.Popen | None:
    if _is_backend_up():
        print("[ok] backend already running on :8000")
        return None

    if not BACKEND_PY.exists():
        raise RuntimeError("backend venv missing. create backend/.venv first")

    env = os.environ.copy()
    env["MONGO_URL"] = env.get("MONGO_URL", "mongodb://127.0.0.1:27017")
    proc = subprocess.Popen(
        [str(BACKEND_PY), "main.py"],
        cwd=str(BACKEND_DIR),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    deadline = time.time() + 12
    while time.time() < deadline:
        if _is_backend_up():
            print("[ok] backend started")
            return proc
        time.sleep(0.4)

    out = ""
    if proc.stdout:
        try:
            out = proc.stdout.read()
        except Exception:
            pass
    proc.terminate()
    raise RuntimeError(f"backend failed to start. logs:\n{out}")


def _count(path: str) -> int:
    data = _http_json(f"http://127.0.0.1:8000/{path}/")
    if isinstance(data, list):
        return len(data)
    return 0


def main() -> int:
    backend_proc = None
    dh_proc = None
    try:
        print("[step] direct weather station validation")
        direct = subprocess.run(
            [
                str(DH_PY),
                str(DIRECT_WEATHER_TEST),
                "--samples",
                "3",
                "--sleep",
                "0.2",
                "--max-attempts",
                "15",
            ],
            cwd=str(ROOT),
            text=True,
            capture_output=True,
            timeout=60,
        )
        print(direct.stdout.strip())
        if direct.returncode != 0:
            print(direct.stderr.strip())
            return direct.returncode

        backend_proc = _start_backend_if_needed()

        before_weather = _count("weather")
        before_ossd = _count("ossd")
        print(f"[info] before weather={before_weather} ossd={before_ossd}")

        if not DH_PY.exists():
            raise RuntimeError("witterungsstation_py/.venv missing")

        env = os.environ.copy()
        env["DATA_HANDLER_OUTPUT"] = "backend"
        env["BACKEND_BASE"] = "http://127.0.0.1:8000"
        env.setdefault("DATA_HANDLER_POLL_SEC", "0.2")
        env.setdefault("DATA_HANDLER_INTERVAL_SEC", "3")

        dh_proc = subprocess.Popen(
            [str(DH_PY), str(DATA_HANDLER_ENTRY)],
            cwd=str(ROOT),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        # let real hardware pipeline run briefly
        time.sleep(8)

        after_weather = _count("weather")
        after_ossd = _count("ossd")
        print(f"[info] after weather={after_weather} ossd={after_ossd}")

        improved_weather = after_weather > before_weather
        improved_ossd = after_ossd > before_ossd

        if improved_weather or improved_ossd:
            print("[ok] pipeline ingestion changed backend state")
            return 0

        print("[warn] no backend count increased. dumping handler output...")
        if dh_proc.stdout:
            try:
                print(dh_proc.stdout.read())
            except Exception:
                pass
        return 2
    except urllib.error.URLError as exc:
        print(f"[fail] backend HTTP error: {exc}")
        return 3
    except Exception as exc:
        print(f"[fail] {exc}")
        return 1
    finally:
        if dh_proc and dh_proc.poll() is None:
            dh_proc.terminate()
            try:
                dh_proc.wait(timeout=2)
            except Exception:
                dh_proc.kill()
        if backend_proc and backend_proc.poll() is None:
            backend_proc.terminate()
            try:
                backend_proc.wait(timeout=2)
            except Exception:
                backend_proc.kill()


if __name__ == "__main__":
    raise SystemExit(main())
