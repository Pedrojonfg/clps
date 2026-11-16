import type { SitePayload } from "../types";

export const SUN_COLOR = "#e0b93a";
export const EARTH_COLOR = "#6aa5d8";
export const TERRAIN_FILL = "#3a3f47";
export const TERRAIN_LINE = "#c4b8a8";
export const INK = "#f6f7f9";
export const INK_MUTED = "#abb3bf";
export const GRID = "#383e47";
export const OK_COLOR = "#72ca9b";
export const BAD_COLOR = "#fa999c";

const COMPASS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"];
export function compass(azDeg: number): string {
  return COMPASS[Math.round((((azDeg % 360) + 360) % 360) / 45) % 8];
}

/**
 * Horizon elevation at a geographic azimuth. The mask array is indexed by its own azimuth
 * (geographic_az = zero + sign × index_az), per D-20261116-pj-b43a.
 */
export function maskAtGeo(mask: SitePayload["mask"], azDeg: number): number {
  const el = mask.elevation_deg;
  const n = el.length;
  const zero = mask.azimuth_zero_deg ?? 180;
  const sign = mask.azimuth_sign ?? -1;
  const idxAz = (((sign * (azDeg - zero)) % 360) + 360) % 360;
  const f = (idxAz / 360) * n;
  const i = Math.floor(f) % n;
  const t = f - Math.floor(f);
  return el[i] * (1 - t) + el[(i + 1) % n] * t;
}

export function fmtUtc(iso: string): string {
  return iso.replace("T", " ").replace(/:00Z$/, "").replace(/Z$/, "");
}

/** Longest run of consecutive `true`, as [startIndex, length]. */
export function longestRun(flags: boolean[]): [number, number] {
  let best: [number, number] = [0, 0];
  let start = 0;
  let cur = 0;
  flags.forEach((v, i) => {
    if (v) {
      if (cur === 0) start = i;
      cur += 1;
      if (cur > best[1]) best = [start, cur];
    } else cur = 0;
  });
  return best;
}
