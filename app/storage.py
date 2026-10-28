"""Where responses are saved.

- Deployed (Streamlit Community Cloud): a Google Sheet, configured in .streamlit/secrets.toml
  with a `gcp_service_account` table and a `sheet_key` string (see docs/app_setup.md).
  The cloud file system is wiped on every restart, so a CSV there would lose data.
- Local runs and pilots without secrets: data/app_responses/responses.csv (git-ignored).

Both stores expose the same methods, so the app does not care which one it uses:
    started_sequences()  sequences of everyone who has started (non-pilot), for allocation
    log_allocation(rec)  record a start ("allocations" tab / allocations.csv), before Part 1
    append(rec)          save a completed participant (first tab / responses.csv)
"""
from __future__ import annotations

import csv
from pathlib import Path

from logic import ALLOCATION_FIELDS, FIELDNAMES, ROOT

LOCAL_PATH = ROOT / "data" / "app_responses" / "responses.csv"
LOCAL_ALLOC_PATH = ROOT / "data" / "app_responses" / "allocations.csv"
ALLOCATION_TAB = "allocations"


def _sequences_from_rows(rows: list[dict]) -> list[int]:
    out = []
    for r in rows:
        if str(r.get("is_pilot", "")).lower() in ("true", "1"):
            continue
        try:
            out.append(int(r["sequence"]))
        except (KeyError, ValueError, TypeError):
            continue
    return out


def _append_csv(path: Path, fields: list[str], record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    new = not path.exists()
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        if new:
            w.writeheader()
        w.writerow({k: record.get(k, "") for k in fields})


def _read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


class LocalCSVStore:
    name = "local CSV"

    def __init__(self, path: Path = LOCAL_PATH, alloc_path: Path = LOCAL_ALLOC_PATH):
        self.path = path
        self.alloc_path = alloc_path

    def started_sequences(self) -> list[int]:
        return _sequences_from_rows(_read_csv(self.alloc_path))

    def log_allocation(self, record: dict) -> None:
        _append_csv(self.alloc_path, ALLOCATION_FIELDS, record)

    def append(self, record: dict) -> None:
        _append_csv(self.path, FIELDNAMES, record)


def ensure_header(ws, fields: list[str] = FIELDNAMES) -> None:
    """Write the header row into an empty sheet; refuse to touch a sheet that holds other data.

    gspread returns an empty sheet as [] or [[]] depending on the version, so emptiness is
    checked cell by cell rather than with `not values`.
    """
    if ws.row_values(1) == fields:
        return
    values = ws.get_all_values()
    if any(str(cell).strip() for row in values for cell in row):
        raise RuntimeError("The Google Sheet's header row does not match the app's fields.")
    ws.append_row(fields, value_input_option="RAW")


class GoogleSheetStore:
    name = "Google Sheet"

    def __init__(self, service_account_info: dict, sheet_key: str):
        import gspread  # imported lazily so local runs do not need it

        client = gspread.service_account_from_dict(dict(service_account_info))
        sheet = client.open_by_key(sheet_key)
        self.ws = sheet.sheet1  # one row per completed participant
        ensure_header(self.ws)
        try:  # one row per participant who pressed "Begin" (allocation + drop-out tracking)
            self.alloc_ws = sheet.worksheet(ALLOCATION_TAB)
        except gspread.WorksheetNotFound:
            self.alloc_ws = sheet.add_worksheet(ALLOCATION_TAB, rows=2000, cols=len(ALLOCATION_FIELDS))
        ensure_header(self.alloc_ws, ALLOCATION_FIELDS)

    def started_sequences(self) -> list[int]:
        return _sequences_from_rows(self.alloc_ws.get_all_records())

    def log_allocation(self, record: dict) -> None:
        self.alloc_ws.append_row([str(record.get(k, "")) for k in ALLOCATION_FIELDS], value_input_option="RAW")

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
