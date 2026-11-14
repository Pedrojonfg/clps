"""Parse Horizons apparent azimuth/elevation tables saved as fixtures.

Rows lie between $$SOE and $$EOE. After the calendar timestamp the CSV
columns are solar-presence, interferer-presence, Azi_(a-app), Elev_(a-app).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

_MONTHS = (
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
)


@dataclass(frozen=True)
class HorizonsRow:
    time_utc: np.datetime64
    az_deg: float
    el_deg: float


def parse_horizons_azel(path: Path | str) -> list[HorizonsRow]:
    file = Path(path)
    text = file.read_text(encoding="utf-8")
    header, marker, rest = text.partition("$$SOE")
    if not marker:
        raise ValueError(f"{file} has no $$SOE marker")
    if "Azi_(a-app)" not in header or "Elev_(a-app)" not in header:
        raise ValueError(f"{file} is missing Azi_(a-app) and Elev_(a-app)")
    block, marker, _tail = rest.partition("$$EOE")
    if not marker:
        raise ValueError(f"{file} has no $$EOE marker")

    rows: list[HorizonsRow] = []
    seen: set[np.datetime64] = set()
    for line in block.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        parts = [part.strip() for part in stripped.split(",")]
        if len(parts) < 5 or not parts[0] or not parts[3] or not parts[4]:
            raise ValueError(f"{file}: short data row {stripped!r}")
        when = _parse_utc(parts[0])
        if when in seen:
            raise ValueError(f"{file}: duplicate timestamp {when}")
        seen.add(when)
        rows.append(HorizonsRow(when, float(parts[3]), float(parts[4])))
    if not rows:
        raise ValueError(f"{file}: no rows between $$SOE and $$EOE")
    return rows


def _parse_utc(token: str) -> np.datetime64:
    """Horizons CAL time, e.g. '2027-Jan-01 00:00', as UTC datetime64[s]."""
    date_token, hm = token.split()
    year_s, mon_s, day_s = date_token.split("-")
    hour_s, minute_s = hm.split(":")
    month = _MONTHS.index(mon_s) + 1
    iso = (
        f"{int(year_s):04d}-{month:02d}-{int(day_s):02d}"
        f"T{int(hour_s):02d}:{int(minute_s):02d}:00"
    )
    return np.datetime64(iso, "s")
