"""Where responses are saved.

- Deployed (Streamlit Community Cloud): a Google Sheet, configured in .streamlit/secrets.toml
  with a `gcp_service_account` table and a `sheet_key` string (see docs/app_setup.md).
  The cloud file system is wiped on every restart, so a CSV there would lose data.
- Local runs and pilots without secrets: data/app_responses/responses.csv (git-ignored).

Both stores expose the same two methods, so the app does not care which one it uses.
"""
from __future__ import annotations

import csv
from pathlib import Path

from logic import FIELDNAMES, ROOT

LOCAL_PATH = ROOT / "data" / "app_responses" / "responses.csv"


def _completed_from_rows(rows: list[dict]) -> list[int]:
    out = []
    for r in rows:
        if str(r.get("is_pilot", "")).lower() in ("true", "1"):
            continue
        try:
            out.append(int(r["sequence"]))
        except (KeyError, ValueError, TypeError):
            continue
    return out


class LocalCSVStore:
    name = "local CSV"

    def __init__(self, path: Path = LOCAL_PATH):
        self.path = path

    def completed_sequences(self) -> list[int]:
        if not self.path.exists():
            return []
        with open(self.path, newline="", encoding="utf-8") as f:
            return _completed_from_rows(list(csv.DictReader(f)))

    def append(self, record: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        new = not self.path.exists()
        with open(self.path, "a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=FIELDNAMES)
            if new:
                w.writeheader()
            w.writerow({k: record.get(k, "") for k in FIELDNAMES})


class GoogleSheetStore:
    name = "Google Sheet"

    def __init__(self, service_account_info: dict, sheet_key: str):
        import gspread  # imported lazily so local runs do not need it

        client = gspread.service_account_from_dict(dict(service_account_info))
        self.ws = client.open_by_key(sheet_key).sheet1
        if self.ws.row_values(1) != FIELDNAMES:
            if not self.ws.get_all_values():
                self.ws.append_row(FIELDNAMES, value_input_option="RAW")
            else:
                raise RuntimeError("The Google Sheet's header row does not match the app's fields.")

    def completed_sequences(self) -> list[int]:
        return _completed_from_rows(self.ws.get_all_records())

    def append(self, record: dict) -> None:
        self.ws.append_row([str(record.get(k, "")) for k in FIELDNAMES], value_input_option="RAW")


def get_store(secrets) -> LocalCSVStore | GoogleSheetStore:
    try:
        has_sheet = "gcp_service_account" in secrets and "sheet_key" in secrets
    except Exception:  # no secrets.toml at all
        has_sheet = False
    if has_sheet:  # errors here should surface: a misconfigured sheet must not silently fall back
        return GoogleSheetStore(secrets["gcp_service_account"], secrets["sheet_key"])
    return LocalCSVStore()
