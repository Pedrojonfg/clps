"""Moon surface hazards provider (P13 decisions)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from moonpark.hazards.lst import local_solar_time_h_from_utc
from moonpark.hazards.pcp import PolarPcpClimatology
from moonpark.hazards.raster import sample_geotiff
from moonpark.hazards.soil import soil_provenance, soil_resistance
from moonpark.hazards.temperature import ClimatologyTable, RasterClimatology
from moonpark.providers import Site

DATA_ROOT = Path(__file__).resolve().parents[2] / "data"
PSR_MESSAGE = "This site lies in a permanently shadowed region; landing is not viable."

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

    def _slope_deg(self, site: Site) -> float:
        if self.slope_path is None or not self.slope_path.is_file():
            return 0.0
        val = sample_geotiff(self.slope_path, site.lat_deg, site.lon_deg)
        return float(val) if val is not None else 0.0

    def _temperature(self, site: Site, time_utc: np.datetime64) -> tuple[float | None, dict]:
        if self.climatology is None:
            return None, {"status": "no_climatology_configured"}
        if isinstance(self.climatology, ClimatologyTable):
            lst = local_solar_time_h_from_utc(time_utc, site.lon_deg)
            return self.climatology.at_lst(lst)
        if isinstance(self.climatology, PolarPcpClimatology):
            return self.climatology.at_site_time(time_utc, site.lat_deg, site.lon_deg)
        return self.climatology.at_site_time(time_utc, site.lon_deg)

    def _temperature_sigma(self, site: Site, time_utc: np.datetime64) -> float | None:
        if isinstance(self.climatology, PolarPcpClimatology):
            return self.climatology.sigma_at_site_time(time_utc, site.lat_deg, site.lon_deg)
        return None

    def hazards(self, site: Site, times: NDArray[np.datetime64]) -> dict:
        if isinstance(self.climatology, PolarPcpClimatology):
            self.climatology.preload(times, site.lon_deg)
        psr = self._psr(site)
        slope_deg = self._slope_deg(site)
        resistance = soil_resistance(slope_deg)
        hours: list[dict] = []
        for time_utc in times:
            temp_k, temp_prov = self._temperature(site, time_utc)
            hours.append(
                {
                    "temperature_k": temp_k,
                    "temperature_sigma_k": None,
                    "soil_resistance": resistance,
                    "slope_deg": slope_deg,
                    "psr": dict(psr),
                    "provenance": {
                        "temperature": temp_prov,
                        "soil_resistance": {
                            **soil_provenance(slope_deg),
                            "label": self.soil_label,
                        },
                        "psr": {"product": "LPSR_80S_20MPP_ADJ", **psr},
                    },
                }
            )
        aggregate = aggregate_hazards(hours)
        # The spread is costly (several PCP bins); compute it only for the hours that set the limits:
        # the hottest hour for the maximum, the coldest for the minimum.
        by_hour = {id(h): t for h, t in zip(hours, times, strict=True)}
        with_t = [h for h in hours if h["temperature_k"] is not None]
        hot = max(with_t, key=lambda h: h["temperature_k"]) if with_t else None
        cold = min(with_t, key=lambda h: h["temperature_k"]) if with_t else None
        if hot is not None:
            aggregate["temperature_sigma_k"] = hot["temperature_sigma_k"] = self._temperature_sigma(
                site, by_hour[id(hot)]
            )
        if cold is not None:
            aggregate["temperature_min_sigma_k"] = cold["temperature_sigma_k"] = (
                aggregate["temperature_sigma_k"] if cold is hot else self._temperature_sigma(site, by_hour[id(cold)])
            )
        return {"hours": hours, "aggregate": aggregate, "psr_precheck": psr}


def aggregate_hazards(hours: list[dict]) -> dict:
    """Worst-case scalars for score(series, hazards, needs)."""
    temps = [h["temperature_k"] for h in hours if h["temperature_k"] is not None]
    return {
        "temperature_k": max(temps) if temps else None,
        "temperature_min_k": min(temps) if temps else None,
        "temperature_sigma_k": None,  # filled by MoonHazards.hazards for the hottest hour
        "temperature_min_sigma_k": None,  # ... and for the coldest hour
        "soil_resistance": min(h["soil_resistance"] for h in hours) if hours else None,
        "slope_deg": hours[0]["slope_deg"] if hours else 0.0,
        "psr": hours[0]["psr"] if hours else {"in_psr": False, "message": None},
    }


_DEFAULT_MOON: MoonHazards | None = None


def default_moon_hazards() -> MoonHazards:
    """Process-wide MoonHazards so PCP bin caches survive across /site calls."""
    global _DEFAULT_MOON
    if _DEFAULT_MOON is None:
        _DEFAULT_MOON = MoonHazards()
    return _DEFAULT_MOON
