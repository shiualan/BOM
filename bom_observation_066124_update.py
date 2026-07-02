#!/usr/bin/env python3

import csv
import json
import subprocess
from pathlib import Path
from datetime import datetime

# -----------------------------
# Configuration
# -----------------------------

REPO_DIR = Path.home() / "Github" / "BOM"

BOM_URL = "https://www.bom.gov.au/fwo/IDN60801/IDN60801.94764.json"

RAW_JSON_FILE = REPO_DIR / "latest_bom_066124_raw.json"
LOG_FILE = REPO_DIR / "bom_parramatta_observations.csv"
OUTPUT_FILE = REPO_DIR / "066124.md"

# Only save this observation
TARGET_SORT_ORDER = 0


# -----------------------------
# Helpers
# -----------------------------

def run_command(command, cwd=None, check=True):
    result = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )

    if check and result.returncode != 0:
        raise RuntimeError(
            f"Command failed: {' '.join(command)}\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

    return result


def fetch_bom_json():
    result = run_command(
        [
            "curl",
            "-fsSL",
            "--retry", "3",
            "--retry-delay", "5",
            "-A", "Mozilla/5.0",
            BOM_URL,
        ]
    )

    RAW_JSON_FILE.write_text(result.stdout, encoding="utf-8")
    return json.loads(result.stdout)


def get_refresh_message(payload):
    headers = payload.get("observations", {}).get("header", [])

    if not headers:
        raise ValueError("No observations.header found in BOM JSON")

    refresh_message = headers[0].get("refresh_message")

    if not refresh_message:
        raise ValueError("No refresh_message found in BOM JSON header")

    return refresh_message


def get_target_observation(payload):
    data = payload.get("observations", {}).get("data", [])

    for item in data:
        if item.get("sort_order") == TARGET_SORT_ORDER:
            return item

    raise ValueError(f"No observation found with sort_order == {TARGET_SORT_ORDER}")


def normalise_value(value):
    if value is None:
        return "-"
    if value == "":
        return "-"
    return value


def append_log(refresh_message, observation):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    row = {
        "logged_at_local": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "refresh_message": refresh_message,
        "sort_order": observation.get("sort_order"),
        "wmo": observation.get("wmo"),
        "name": observation.get("name"),
        "local_date_time": observation.get("local_date_time"),
        "local_date_time_full": observation.get("local_date_time_full"),
        "aifstime_utc": observation.get("aifstime_utc"),
        "air_temp": observation.get("air_temp"),
        "apparent_t": observation.get("apparent_t"),
        "dewpt": observation.get("dewpt"),
        "rel_hum": observation.get("rel_hum"),
        "delta_t": observation.get("delta_t"),
        "cloud": observation.get("cloud"),
        "cloud_base_m": observation.get("cloud_base_m"),
        "cloud_oktas": observation.get("cloud_oktas"),
        "weather": observation.get("weather"),
        "wind_dir": observation.get("wind_dir"),
        "wind_spd_kmh": observation.get("wind_spd_kmh"),
        "gust_kmh": observation.get("gust_kmh"),
        "wind_spd_kt": observation.get("wind_spd_kt"),
        "gust_kt": observation.get("gust_kt"),
        "press_qnh": observation.get("press_qnh"),
        "press_msl": observation.get("press_msl"),
        "rain_trace": observation.get("rain_trace"),
        "vis_km": observation.get("vis_km"),
    }

    file_exists = LOG_FILE.exists()

    with LOG_FILE.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))

        if not file_exists:
            writer.writeheader()

        writer.writerow(row)


def build_readme(refresh_message, observation):
    station_name = normalise_value(observation.get("name"))
    local_date_time = normalise_value(observation.get("local_date_time"))

    table = f"""# BOM Parramatta Latest Observation

Source:

`{BOM_URL}`

## Latest issue time

{refresh_message}

## Latest observation

| Field | Value |
| --- | --- |
| Station | {station_name} |
| Date/Time EST | {local_date_time} |
| Temperature | {normalise_value(observation.get("air_temp"))} °C |
| Apparent Temperature | {normalise_value(observation.get("apparent_t"))} °C |
| Dew Point | {normalise_value(observation.get("dewpt"))} °C |
| Relative Humidity | {normalise_value(observation.get("rel_hum"))}% |
| Delta-T | {normalise_value(observation.get("delta_t"))} °C |
| Weather | {normalise_value(observation.get("weather"))} |
| Cloud | {normalise_value(observation.get("cloud"))} |
| Visibility | {normalise_value(observation.get("vis_km"))} km |
| Wind Direction | {normalise_value(observation.get("wind_dir"))} |
| Wind Speed | {normalise_value(observation.get("wind_spd_kmh"))} km/h |
| Wind Gust | {normalise_value(observation.get("gust_kmh"))} km/h |
| Wind Speed | {normalise_value(observation.get("wind_spd_kt"))} kts |
| Wind Gust | {normalise_value(observation.get("gust_kt"))} kts |
| Pressure QNH | {normalise_value(observation.get("press_qnh"))} hPa |
| Pressure MSL | {normalise_value(observation.get("press_msl"))} hPa |
| Rain since 9am | {normalise_value(observation.get("rain_trace"))} mm |

## Latest observation table

| Date/Time EST | Temp °C | App Temp °C | Dew Point °C | Rel Hum % | Delta-T °C | Wind Dir | Wind Spd km/h | Wind Gust km/h | Wind Spd kts | Wind Gust kts | Press QNH hPa | Press MSL hPa | Rain since 9am mm |
| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| {local_date_time} | {normalise_value(observation.get("air_temp"))} | {normalise_value(observation.get("apparent_t"))} | {normalise_value(observation.get("dewpt"))} | {normalise_value(observation.get("rel_hum"))} | {normalise_value(observation.get("delta_t"))} | {normalise_value(observation.get("wind_dir"))} | {normalise_value(observation.get("wind_spd_kmh"))} | {normalise_value(observation.get("gust_kmh"))} | {normalise_value(observation.get("wind_spd_kt"))} | {normalise_value(observation.get("gust_kt"))} | {normalise_value(observation.get("press_qnh"))} | {normalise_value(observation.get("press_msl"))} | {normalise_value(observation.get("rain_trace"))} |

## Files

| File | Purpose |
| --- | --- |
| `latest_bom_raw.json` | Latest raw JSON downloaded from BOM |
| `bom_parramatta_observations.csv` | Append-only observation log for `sort_order == 0` |
| `README.md` | Latest readable observation summary |

Last updated locally by script: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

    OUTPUT_FILE.write_text(table, encoding="utf-8")


def git_commit_and_push(refresh_message):
    run_command(["git", "add", "."], cwd=REPO_DIR)

    status = run_command(
        ["git", "status", "--porcelain"],
        cwd=REPO_DIR,
        check=True,
    )

    if not status.stdout.strip():
        print("No changes to commit.")
        return

    safe_message = refresh_message.strip()

    run_command(
        ["git", "commit", "-m", safe_message],
        cwd=REPO_DIR,
    )

    run_command(
        ["git", "push"],
        cwd=REPO_DIR,
    )


def main():
    if not REPO_DIR.exists():
        raise FileNotFoundError(f"Repository folder does not exist: {REPO_DIR}")

    payload = fetch_bom_json()
    refresh_message = get_refresh_message(payload)
    observation = get_target_observation(payload)

    append_log(refresh_message, observation)
    build_readme(refresh_message, observation)
    git_commit_and_push(refresh_message)

    print(f"Updated BOM observation: {refresh_message}")


if __name__ == "__main__":
    main()
