from __future__ import annotations

import argparse
import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path
import sys
from typing import Callable

APP_ROOT = Path(__file__).resolve().parent
REPO_ROOT = APP_ROOT.parent
for path in (APP_ROOT, REPO_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from model.system_clock import SystemClock


def env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    try:
        return int(value) if value is not None else default
    except Exception:
        return default


@dataclass
class WeatherSanity:
    temp_ok: bool
    pressure_ok: bool
    humidity_ok: bool
    wind_ok: bool
    rain_ok: bool
    light_ok: bool


def _check_sample(sample) -> WeatherSanity:
    return WeatherSanity(
        temp_ok=(-50.0 <= float(sample.temp) <= 60.0),
        pressure_ok=(850.0 <= float(sample.pressure) <= 1200.0),
        humidity_ok=(0.0 <= float(sample.humidity) <= 100.0),
        wind_ok=(0.0 <= float(sample.winds) <= 120.0),
        rain_ok=(0.0 <= float(sample.rain) <= 500.0),
        light_ok=(0.0 <= float(sample.light) <= 2_000_000.0),
    )


def _render_sanity(sanity: WeatherSanity) -> str:
    flags = asdict(sanity)
    bad = [name for name, ok in flags.items() if not ok]
    if not bad:
        return "OK"
    return f"WARN({', '.join(bad)})"


def run_manual_test(
    *,
    samples: int,
    delay_sec: float,
    log: Callable[[str], None],
) -> int:
    try:
        from model.hid_sensor import HidWeatherSensor
    except ModuleNotFoundError as error:
        log(f"Cannot start manual weather USB test: missing dependency ({error})")
        log("Install Python dependencies first (hid/hidapi missing).")
        return 3

    clock = SystemClock()

    vid = env_int("HID_VID", 0x1941)
    pid = env_int("HID_PID", 0x8021)

    try:
        sensor = HidWeatherSensor(vid=vid, pid=pid, clock=clock, log=log)
    except Exception as error:
        log(f"Cannot initialize HID weather sensor: {error}")
        return 4

    log(f"Manual weather USB test started (VID=0x{vid:04X}, PID=0x{pid:04X})")
    log("Tip: set WEATHER_DEBUG=1 to print raw HID pointer/bytes from the adapter.")

    ok_count = 0
    for index in range(samples):
        reading = sensor.read_weather()
        if reading is None:
            log(f"[{index + 1}/{samples}] no reading")
        else:
            sanity = _check_sample(reading)
            status = _render_sanity(sanity)
            if status == "OK":
                ok_count += 1

            log(
                f"[{index + 1}/{samples}] {status} "
                f"temp={reading.temp}C pressure={reading.pressure}hPa humidity={reading.humidity}% "
                f"wind={reading.winds}km/h dir={reading.winddir} rain={reading.rain} light={reading.light}"
            )

        if index + 1 < samples:
            time.sleep(delay_sec)

    log(f"Completed manual weather USB test: {ok_count}/{samples} within sanity ranges")
    if ok_count == 0:
        log(
            "Hint: if all reads are empty but lsusb shows the device, "
            "check hidraw permissions/udev rules for non-root access."
        )
        return 2
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Manual weather-station USB read test")
    parser.add_argument("--samples", type=int, default=10, help="Number of readings to capture")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay in seconds between readings")
    args = parser.parse_args()

    samples = max(1, int(args.samples))
    delay_sec = max(0.1, float(args.delay))

    return run_manual_test(samples=samples, delay_sec=delay_sec, log=print)


if __name__ == "__main__":
    raise SystemExit(main())
