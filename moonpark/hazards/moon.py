"""Moon surface hazards provider (P13 decisions)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from moonpark.hazards.lst import HazardDataUnavailable, local_solar_time_h_from_utc
from moonpark.hazards.pcp import PolarPcpClimatology
from moonpark.hazards.raster import sample_geotiff, sample_geotiff_status
from moonpark.hazards.soil import soil_provenance, soil_resistance
from moonpark.hazards.temperature import ClimatologyTable, RasterClimatology
from moonpark.providers import Site

DATA_ROOT = Path(__file__).resolve().parents[2] / "data"
PSR_MESSAGE = "This site lies in a permanently shadowed region; landing is not viable."

# Short reasons for hazards that could not be evaluated ("not evaluated" + a two-three word hover,
# D-20261118-pj-b3dc payload_label_for_unavailable_hazard). Keyed by the provenance status code.
SLOPE_UNAVAILABLE_REASON = {
    "missing_file": "slope data missing",
    "unreadable": "slope data unreadable",
    "outside_raster": "outside slope map",
    "nodata": "no slope value",
}
TEMPERATURE_UNAVAILABLE_REASON = {
    "no_climatology_configured": "temperature data missing",
    "missing_pcp_bin": "temperature bin missing",
    "missing_bin": "temperature bin missing",
    "empty_window": "temperature bin missing",
    "no_points_in_radius": "outside temperature map",
    "unfilled": "outside temperature map",
    "ephemeris_unavailable": "season not computable",
}

def _data_file(rel: str) -> Path | None:
    from moonpark.horizon.remote import locate

    return locate(rel)


Climatology = ClimatologyTable | RasterClimatology | PolarPcpClimatology


@dataclass
class MoonHazards:
    slope_path: Path | None = None
    psr_path: Path | None = None
    climatology: Climatology | None = None
    soil_label: str = "soil_erodibility_resistance_not_lofting_rate"

    def __post_init__(self) -> None:
        if self.slope_path is None:
            self.slope_path = _data_file("dem/LDSM_80S_80MPP_ADJ.TIF")
        if self.psr_path is None:
            self.psr_path = _data_file("dem/LPSR_80S_20MPP_ADJ.TIF")
        if self.climatology is None:
            pcp = PolarPcpClimatology()
            if pcp.available():
                self.climatology = pcp

    def _psr(self, site: Site) -> dict:
        if self.psr_path is None or not self.psr_path.is_file():
            return {"in_psr": False, "message": None}
        val = sample_geotiff(self.psr_path, site.lat_deg, site.lon_deg)
        in_psr = val is not None and val > 0.5
        return {
            "in_psr": in_psr,
            "message": PSR_MESSAGE if in_psr else None,
        }

    def _slope(self, site: Site) -> tuple[float | None, str]:
        """(slope_deg, status). Missing file, site outside the raster or a NoData pixel give None, never
        0 deg (D-20261118-pj-b3dc; outside coverage counts as missing data)."""
        if self.slope_path is None:
            return None, "missing_file"
        return sample_geotiff_status(self.slope_path, site.lat_deg, site.lon_deg)

    def _slope_deg(self, site: Site) -> float | None:
        return self._slope(site)[0]

    def _temperature(self, site: Site, time_utc: np.datetime64) -> tuple[float | None, dict]:
        if self.climatology is None:
            return None, {"status": "no_climatology_configured"}
        try:
            if isinstance(self.climatology, ClimatologyTable):
                lst = local_solar_time_h_from_utc(time_utc, site.lon_deg)
                return self.climatology.at_lst(lst)
            if isinstance(self.climatology, PolarPcpClimatology):
                return self.climatology.at_site_time(time_utc, site.lat_deg, site.lon_deg)
            return self.climatology.at_site_time(time_utc, site.lon_deg)
        except HazardDataUnavailable as exc:
            # Season / local time not computable: no guessed season, the temperature is not evaluated.
            return None, {"status": "ephemeris_unavailable", "error": str(exc)}

    def _temperature_sigma(self, site: Site, time_utc: np.datetime64) -> float | None:
        if isinstance(self.climatology, PolarPcpClimatology):
            return self.climatology.sigma_at_site_time(time_utc, site.lat_deg, site.lon_deg)
        return None

    def hazards(self, site: Site, times: NDArray[np.datetime64]) -> dict:
        """Hourly hazards plus worst-case aggregate. Fields whose program data is missing are None and are
        listed under "unavailable" ({field: short reason}, empty when nothing is missing), at the top level
        and in "aggregate". Missing PSR map is not listed (skipped silently). # per D-20261118-pj-b3dc"""
        if isinstance(self.climatology, PolarPcpClimatology):
            try:
                self.climatology.preload(times, site.lon_deg)
            except HazardDataUnavailable:
                pass  # each hour then reports the temperature as not evaluated
        psr = self._psr(site)
        slope_deg, slope_status = self._slope(site)
        resistance = soil_resistance(slope_deg)
        soil_prov = {**soil_provenance(slope_deg), "label": self.soil_label}
        if slope_deg is None:
            soil_prov["status"] = slope_status
            soil_prov["reason"] = SLOPE_UNAVAILABLE_REASON.get(slope_status, "slope data missing")
        hours: list[dict] = []
        for time_utc in times:
            temp_k, temp_prov = self._temperature(site, time_utc)
            if temp_k is None:
                status = temp_prov.get("status", "")
                temp_prov = {**temp_prov, "reason": TEMPERATURE_UNAVAILABLE_REASON.get(status, "temperature data missing")}
            hours.append(
                {
                    "temperature_k": temp_k,
                    "temperature_sigma_k": None,
                    "soil_resistance": resistance,
                    "slope_deg": slope_deg,
                    "psr": dict(psr),
                    "provenance": {
                        "temperature": temp_prov,
                        "soil_resistance": dict(soil_prov),
                        "psr": {"product": "LPSR_80S_20MPP_ADJ", **psr},
                    },
                }
            )
        aggregate = aggregate_hazards(hours)
        # The spread is costly (several PCP bins); compute it only for the hours that set the limits:
        # the hottest hour for the maximum, the coldest for the minimum. Skipped when the temperature is
        # not evaluated (some hour missing).
        if aggregate["temperature_k"] is not None:
            by_hour = {id(h): t for h, t in zip(hours, times, strict=True)}
            hot = max(hours, key=lambda h: h["temperature_k"])
            cold = min(hours, key=lambda h: h["temperature_k"])
            try:
                aggregate["temperature_sigma_k"] = hot["temperature_sigma_k"] = self._temperature_sigma(
                    site, by_hour[id(hot)]
                )
                aggregate["temperature_min_sigma_k"] = cold["temperature_sigma_k"] = (
                    aggregate["temperature_sigma_k"]
                    if cold is hot
                    else self._temperature_sigma(site, by_hour[id(cold)])
                )
            except HazardDataUnavailable:
                pass  # sigma is optional context; the temperature itself was already evaluated
        return {
            "hours": hours,
            "aggregate": aggregate,
            "psr_precheck": psr,
            "unavailable": dict(aggregate["unavailable"]),
        }


def _unavailable_reason(hour: dict, field: str, default: str) -> str:
    prov = (hour.get("provenance") or {}).get(field) or {}
    reason = prov.get("reason") if isinstance(prov, dict) else None
    return reason if isinstance(reason, str) and reason else default


def aggregate_hazards(hours: list[dict]) -> dict:
    """Worst-case scalars for score(series, hazards, needs).

    A field missing in any hour is None in the aggregate (no partial worst case: the missing hour may be
    the worst one) and is listed in "unavailable" with a short reason. # per D-20261118-pj-b3dc"""
    unavailable: dict[str, str] = {}
    temps = [h.get("temperature_k") for h in hours]
    temp_missing = [h for h, t in zip(hours, temps, strict=True) if t is None]
    if temp_missing:
        unavailable["temperature"] = _unavailable_reason(temp_missing[0], "temperature", "temperature data missing")
    res = [h.get("soil_resistance") for h in hours]
    res_missing = [h for h, r in zip(hours, res, strict=True) if r is None]
    if res_missing:
        unavailable["soil_resistance"] = _unavailable_reason(res_missing[0], "soil_resistance", "slope data missing")
    temps_ok = hours and not temp_missing
    return {
        "temperature_k": max(temps) if temps_ok else None,
        "temperature_min_k": min(temps) if temps_ok else None,
        "temperature_sigma_k": None,  # filled by MoonHazards.hazards for the hottest hour
        "temperature_min_sigma_k": None,  # ... and for the coldest hour
        "soil_resistance": min(res) if hours and not res_missing else None,
        "slope_deg": hours[0].get("slope_deg") if hours else None,
        "psr": hours[0]["psr"] if hours else {"in_psr": False, "message": None},
        "unavailable": unavailable,
    }


_DEFAULT_MOON: MoonHazards | None = None


def default_moon_hazards() -> MoonHazards:
    """Process-wide MoonHazards so PCP bin caches survive across /site calls."""
    global _DEFAULT_MOON
    if _DEFAULT_MOON is None:
        _DEFAULT_MOON = MoonHazards()
    return _DEFAULT_MOON
