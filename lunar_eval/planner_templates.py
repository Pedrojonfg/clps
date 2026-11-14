"""Mission need presets for the demo UI. # per D-20261114-pj-8588 D-20261114-pj-f369"""

from __future__ import annotations

from typing import Any

# Heritage: D-f369 (Blue Ghost ~5 h battery, VIPER 50/70 h darkness, Artemis III continuous light).
# Numbers are planning defaults, not certified mission requirements.

TEMPLATES: dict[str, dict[str, Any]] = {
    "blue_ghost_m1": {
        "label": "Firefly Blue Ghost (CLPS M1)",
        "description": "Short post-sunset battery horizon (~5 h) from D-f369 Blue Ghost M1 note.",
        "max_night_h": 5,
        "max_no_earth_h": 48,
        "require_both": False,
        "sun_lit_percent": 0,
        "earth_lit_percent": 0,
        "bridge_h": 5,
    },
    "viper_nominal": {
        "label": "VIPER hibernation (nominal)",
        "description": "50 h continuous darkness planning figure cited in D-f369.",
        "max_night_h": 50,
        "max_no_earth_h": 24,
        "require_both": False,
        "sun_lit_percent": 0,
        "earth_lit_percent": 0,
        "bridge_h": 5,
    },
    "viper_requirement": {
        "label": "VIPER (conservative / 70 h)",
        "description": "70 h darkness requirement note in D-f369 checks.",
        "max_night_h": 70,
        "max_no_earth_h": 24,
        "require_both": False,
        "sun_lit_percent": 0,
        "earth_lit_percent": 0,
        "bridge_h": 9,
    },
    "artemis_iii_stay": {
        "label": "Artemis III surface stay",
        "description": "Favour continuous Sun and Earth windows (D-f369 Artemis III note).",
        "max_night_h": 24,
        "max_no_earth_h": 12,
        "require_both": True,
        "sun_lit_percent": 50,
        "earth_lit_percent": 50,
        "bridge_h": 5,
    },
    "clps_average": {
        "label": "CLPS portfolio average",
        "description": "Balanced default used in early mock API.",
        "max_night_h": 72,
        "max_no_earth_h": 48,
        "require_both": False,
        "sun_lit_percent": 0,
        "earth_lit_percent": 0,
        "bridge_h": 5,
    },
    "intuitive_moderate": {
        "label": "IM-class moderate night",
        "description": "Mid CLPS night cap for polar power budgeting.",
        "max_night_h": 24,
        "max_no_earth_h": 36,
        "require_both": False,
        "sun_lit_percent": 10,
        "earth_lit_percent": 0,
        "bridge_h": 5,
    },
    "astrobotic_conservative": {
        "label": "Astrobotic-class conservative",
        "description": "Tight darkness and comm gap for small landers.",
        "max_night_h": 12,
        "max_no_earth_h": 24,
        "require_both": False,
        "sun_lit_percent": 0,
        "earth_lit_percent": 0,
        "bridge_h": 5,
    },
    "dte_relay_priority": {
        "label": "Direct-to-Earth priority",
        "description": "Short gaps without Earth visibility.",
        "max_night_h": 48,
        "max_no_earth_h": 8,
        "require_both": False,
        "sun_lit_percent": 0,
        "earth_lit_percent": 25,
        "bridge_h": 5,
    },
    "power_survival": {
        "label": "Long polar night survival",
        "description": "Stress case for extended darkness tolerance.",
        "max_night_h": 120,
        "max_no_earth_h": 72,
        "require_both": False,
        "sun_lit_percent": 0,
        "earth_lit_percent": 0,
        "bridge_h": 5,
    },
    "polar_scout": {
        "label": "Polar scout / survey",
        "description": "Modest thresholds with partial-disc light definition.",
        "max_night_h": 36,
        "max_no_earth_h": 30,
        "require_both": False,
        "sun_lit_percent": 25,
        "earth_lit_percent": 25,
        "bridge_h": 5,
    },
}

DEMO_SITE01 = {"lat_deg": -89.46316, "lon_deg": 222.51045, "label": "PGDA Site01 demo"}


def list_templates() -> list[dict]:
    return [
        {"id": tid, "label": t["label"], "description": t["description"], **{k: t[k] for k in (
            "max_night_h", "max_no_earth_h", "require_both",
            "sun_lit_percent", "earth_lit_percent", "bridge_h",
        )}}
        for tid, t in TEMPLATES.items()
    ]


def template_needs(template_id: str | None) -> dict | None:
    if not template_id:
        return None
    t = TEMPLATES.get(template_id)
    if not t:
        return None
    return {
        "max_night_h": int(t["max_night_h"]),
        "max_no_earth_h": int(t["max_no_earth_h"]),
        "require_both": bool(t["require_both"]),
        "sun_lit_percent": float(t["sun_lit_percent"]),
        "earth_lit_percent": float(t["earth_lit_percent"]),
        "bridge_h": int(t["bridge_h"]),
        "template_id": template_id,
    }