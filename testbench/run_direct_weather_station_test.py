from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data_handler.core import WeatherReader
from shared.hid_client import HidClient, HidConfig
from shared.parsers import WeatherParser


@dataclass
class WeatherValidation:
    has_all_fields: bool
    winddir_ok: bool
    temp_ok: bool
    pressure_ok: bool
    humidity_ok: bool
    winds_ok: bool
    rain_ok: bool
    light_ok: bool

    def all_ok(self) -> bool:
        return all(
            (
                self.temp_ok,
                self.pressure_ok,
                self.humidity_ok,
                self.winddir_ok,
                self.winds_ok,
                self.rain_ok,
                self.light_ok,
            )
        )


def validate_payload(data: dict) -> WeatherValidation:
    required_keys = {"temp", "pressure", "humidity", "winds", "winddir", "rain", "light"}
    has_all_fields = required_keys.issubset(set(data.keys()))
    winddir = str(data.get("winddir", "")).strip().upper()
    valid_dirs = {
        "N", "NNE", "NE", "NEE", "E", "SEE", "SE", "SSE",
        "S", "SSW", "SW", "SWW", "W", "NWW", "NW", "NNW",
    }
    return WeatherValidation(
        has_all_fields=has_all_fields,
        winddir_ok=(winddir in valid_dirs),
        temp_ok=(-50.0 <= float(data.get("temp", 0)) <= 60.0),
        pressure_ok=(850.0 <= float(data.get("pressure", 0)) <= 1200.0),
        humidity_ok=(0.0 <= float(data.get("humidity", 0)) <= 100.0),
        winds_ok=(0.0 <= float(data.get("winds", 0)) <= 120.0),
        rain_ok=(0.0 <= float(data.get("rain", 0)) <= 5000.0),
        light_ok=(0.0 <= float(data.get("light", 0)) <= 2_000_000.0),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Direct weather station read validation")
    parser.add_argument("--samples", type=int, default=5, help="Number of direct reads")
    parser.add_argument("--sleep", type=float, default=0.5, help="Delay between reads in seconds")
    parser.add_argument("--max-attempts", type=int, default=30, help="Maximum read attempts")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    samples = max(1, int(args.samples))
    delay = max(0.0, float(args.sleep))
    max_attempts = max(samples, int(args.max_attempts))

    cfg = HidConfig(vid=0x1941, pid=0x8021, report_size=32)
    client = HidClient(cfg, log=print)
    if not client.open():
        print("[fail] could not open weather station HID transport")
        return 2

    try:
        parser = WeatherParser(log=print)
        reader = WeatherReader(client, parser, print)
        payloads: list[dict] = []
        failed_attempts: list[int] = []

        print(f"[step] reading weather station directly: samples={samples} max_attempts={max_attempts}")
        attempt = 0
        while len(payloads) < samples and attempt < max_attempts:
            attempt += 1
            payload = reader.read()
            if not payload:
                failed_attempts.append(attempt)
            else:
                payloads.append(payload)
                v = validate_payload(payload)
                print(f"[info] sample {len(payloads)} (attempt {attempt}): {payload}")
                if not v.all_ok():
                    print(f"[warn] sample {len(payloads)} failed validation: {v}")
                    return 4

            if len(payloads) < samples and delay > 0.0:
                time.sleep(delay)

        if len(payloads) < samples:
            print(f"[fail] only got {len(payloads)}/{samples} sane payloads within {max_attempts} attempts")
            print(f"[fail] failed attempts: {failed_attempts}")
            return 3

        if not payloads:
            print("[fail] weather reader returned no payloads")
            return 3

        temp_values = [float(x["temp"]) for x in payloads]
        pressure_values = [float(x["pressure"]) for x in payloads]
        humidity_values = [float(x["humidity"]) for x in payloads]
        wind_values = [float(x["winds"]) for x in payloads]
        rain_values = [float(x["rain"]) for x in payloads]
        light_values = [float(x["light"]) for x in payloads]
        dirs = sorted({str(x["winddir"]) for x in payloads})

        print(
            "[info] ranges "
            f"temp={min(temp_values):.2f}..{max(temp_values):.2f} "
            f"pressure={min(pressure_values):.2f}..{max(pressure_values):.2f} "
            f"humidity={min(humidity_values):.2f}..{max(humidity_values):.2f} "
            f"winds={min(wind_values):.2f}..{max(wind_values):.2f} "
            f"rain={min(rain_values):.2f}..{max(rain_values):.2f} "
            f"light={min(light_values):.2f}..{max(light_values):.2f}"
        )
        print(f"[info] winddir values: {dirs}")
        print("[ok] direct weather station reads succeeded with complete, sane payloads")
        return 0
    finally:
        client.close()


if __name__ == "__main__":
    raise SystemExit(main())
