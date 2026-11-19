/**
 * Planner result view (D-20261116-pj-142f): horizon panorama, visibility timeline and
 * needs-versus-actual. One shared time cursor links the panorama and the timeline.
 */
import { useMemo, useRef, useState, type MouseEvent } from "react";
import { Callout, HTMLTable, Icon, Tag } from "@blueprintjs/core";
import {
  BAD_COLOR,
  EARTH_COLOR,
  GRID,
  INK,
  INK_MUTED,
  MONO,
  SUN_COLOR,
  TERRAIN_FILL,
  TERRAIN_LINE,
  compass,
  fmtUtc,
  longestRun,
  maskAtGeo,
} from "./lib/sky";
import type { SitePayload } from "./types";

const SCORE_CEILING = 1.4; // absolute scale shared with the region map (D-7227)
const FONT = 11;

function pct(v: number): string {
  return `${Math.round(100 * v)} %`;
}

function thresholds(data: SitePayload) {
  return {
    sun: Number(data.needs?.sun_lit_threshold ?? 0),
    earth: Number(data.needs?.earth_lit_threshold ?? 0),
  };
}

/** Pointer x inside an SVG drawn with a viewBox, in viewBox units. */
function svgX(ev: MouseEvent<SVGSVGElement>, viewW: number): number {
  const r = ev.currentTarget.getBoundingClientRect();
  return ((ev.clientX - r.left) / r.width) * viewW;
}

/* ------------------------------------------------------------------ panorama */

const PW = 920;
const PH = 300;
const PP = { l: 44, r: 14, t: 18, b: 40 };

type CursorProps = { cursor: number | null; setCursor: (i: number | null) => void };

export function HorizonPanorama({ data, cursor, setCursor }: { data: SitePayload } & CursorProps) {
  const thr = thresholds(data);
  const geom = useMemo(() => {
    const maskPts: [number, number][] = [];
    for (let az = 0; az <= 360; az += 0.5) maskPts.push([az, maskAtGeo(data.mask, az)]);
    const els = [
      ...maskPts.map((p) => p[1]),
      ...data.sky.flatMap((s) => [s.sun_el_deg, s.earth_el_deg]),
    ];
    const lo = Math.max(-12, Math.floor(Math.min(0, ...els) - 0.6));
    const hi = Math.min(60, Math.ceil(Math.max(...els) + 0.8));
    return { maskPts, lo, hi };
  }, [data]);

  const { maskPts, lo, hi } = geom;
  const plotW = PW - PP.l - PP.r;
  const plotH = PH - PP.t - PP.b;
  const X = (az: number) => PP.l + (az / 360) * plotW;
  const Y = (el: number) => PP.t + plotH - ((Math.min(hi, Math.max(lo, el)) - lo) / (hi - lo)) * plotH;

  const span = hi - lo;
  const step = span > 30 ? 10 : span > 14 ? 5 : span > 7 ? 2 : 1;
  const elTicks: number[] = [];
  for (let e = Math.ceil(lo / step) * step; e <= hi; e += step) elTicks.push(e);

  const terrain =
    `M ${X(0)},${PP.t + plotH} ` +
    maskPts.map(([az, el]) => `L ${X(az).toFixed(1)},${Y(el).toFixed(1)}`).join(" ") +
    ` L ${X(360)},${PP.t + plotH} Z`;
  const ridge = maskPts
    .map(([az, el], i) => `${i ? "L" : "M"} ${X(az).toFixed(1)},${Y(el).toFixed(1)}`)
    .join(" ");

  function track(azKey: "sun_az_deg" | "earth_az_deg", elKey: "sun_el_deg" | "earth_el_deg") {
    let d = "";
    let prev: number | null = null;
    for (const s of data.sky) {
      const jump = prev === null || Math.abs(s[azKey] - prev) > 180;
      d += `${jump ? "M" : "L"} ${X(s[azKey]).toFixed(1)},${Y(s[elKey]).toFixed(1)} `;
      prev = s[azKey];
    }
    return d;
  }

  const n = data.sky.length;
  const every = Math.max(1, Math.ceil(n / 72)); // keep sample dots readable on long windows
  const cur = cursor != null ? data.sky[cursor] : null;

  function onMove(ev: MouseEvent<SVGSVGElement>) {
    const r = ev.currentTarget.getBoundingClientRect();
    const mx = svgX(ev, PW);
    const my = ((ev.clientY - r.top) / r.height) * PH;
    let best = -1;
    let bestD = 40 * 40;
    data.sky.forEach((s, i) => {
      for (const [az, el] of [
        [s.sun_az_deg, s.sun_el_deg],
        [s.earth_az_deg, s.earth_el_deg],
      ]) {
        const d = (X(az) - mx) ** 2 + (Y(el) - my) ** 2;
        if (d < bestD) {
          bestD = d;
          best = i;
        }
      }
    });
    setCursor(best >= 0 ? best : null);
  }

  function bodyAt(i: number, which: "sun" | "earth") {
    const s = data.sky[i];
    const az = which === "sun" ? s.sun_az_deg : s.earth_az_deg;
    const el = which === "sun" ? s.sun_el_deg : s.earth_el_deg;
    const frac = (which === "sun" ? data.series.sun_fraction : data.series.earth_fraction)[i];
    const visible = frac > (which === "sun" ? thr.sun : thr.earth);
    return { az, el, frac, visible };
  }

  return (
    <figure style={{ margin: 0 }}>
      <figcaption style={{ display: "flex", gap: 16, alignItems: "baseline", flexWrap: "wrap", marginBottom: 4 }}>
        <strong>Horizon panorama</strong>
        <span style={{ color: INK_MUTED, fontSize: 12 }}>
          What an observer sees turning around: terrain below the line hides the Sun and the Earth.
        </span>
        <span style={{ flex: 1 }} />
        <Legend />
      </figcaption>
      <svg
        viewBox={`0 0 ${PW} ${PH}`}
        width="100%"
        role="img"
        aria-label="Horizon mask by azimuth with the Sun and Earth tracks over the time window"
        style={{ display: "block", background: "#1c2127", borderRadius: 4, maxHeight: "25vh" }}
        onMouseMove={onMove}
        onMouseLeave={() => setCursor(null)}
      >
        {elTicks.map((e) => (
          <g key={e}>
            <line x1={PP.l} x2={PW - PP.r} y1={Y(e)} y2={Y(e)} stroke={GRID} strokeWidth={e === 0 ? 1.2 : 0.6} />
            <text x={PP.l - 6} y={Y(e)} fill={INK_MUTED} fontSize={FONT} textAnchor="end" dominantBaseline="middle">
              {e}°
            </text>
          </g>
        ))}
        {[0, 45, 90, 135, 180, 225, 270, 315, 360].map((az) => (
          <g key={az}>
            <line x1={X(az)} x2={X(az)} y1={PP.t} y2={PP.t + plotH} stroke={GRID} strokeWidth={0.6} />
            <text
              x={X(az)}
              y={PP.t + plotH + 14}
              fill={az % 90 === 0 ? INK : INK_MUTED}
              fontSize={FONT}
              textAnchor={az === 0 ? "start" : az === 360 ? "end" : "middle"}
            >
              {compass(az)} {az}°
            </text>
          </g>
        ))}
        <text x={PP.l + plotW / 2} y={PH - 6} fill={INK_MUTED} fontSize={FONT} textAnchor="middle">
          Azimuth, clockwise from north · elevation axis is stretched
        </text>

        <path d={terrain} fill={TERRAIN_FILL} />
        <path d={ridge} fill="none" stroke={TERRAIN_LINE} strokeWidth={1.6} strokeLinejoin="round" />
        <text x={PP.l + 6} y={PP.t + plotH - 6} fill={INK_MUTED} fontSize={FONT}>
          terrain (our horizon mask)
        </text>

        {(["earth", "sun"] as const).map((which) => {
          const color = which === "sun" ? SUN_COLOR : EARTH_COLOR;
          return (
            <g key={which}>
              <path
                d={track(`${which}_az_deg`, `${which}_el_deg`)}
                fill="none"
                stroke={color}
                strokeWidth={2}
                strokeLinejoin="round"
                opacity={0.55}
              />
              {data.sky.map((_, i) => {
                if (i % every !== 0 && i !== n - 1) return null;
                const b = bodyAt(i, which);
                return (
                  <circle
                    key={i}
                    cx={X(b.az)}
                    cy={Y(b.el)}
                    r={3.2}
                    fill={b.visible ? color : "#1c2127"}
                    stroke={color}
                    strokeWidth={1.4}
                  />
                );
              })}
            </g>
          );
        })}

        {/* Start-of-window labels so each track is named without relying on colour. */}
        {(["sun", "earth"] as const).map((which) => {
          const b = bodyAt(0, which);
          const right = X(b.az) < PW - 120;
          return (
            <text
              key={which}
              x={X(b.az) + (right ? 8 : -8)}
              y={Y(b.el) + (which === "sun" ? 16 : -9)}
              fill={INK}
              fontSize={FONT}
              textAnchor={right ? "start" : "end"}
              style={{ paintOrder: "stroke", stroke: "#1c2127", strokeWidth: 3 }}
            >
              {which === "sun" ? "Sun" : "Earth"} · start
            </text>
          );
        })}

        {cur &&
          cursor != null &&
          (["earth", "sun"] as const).map((which) => {
            const b = bodyAt(cursor, which);
            const color = which === "sun" ? SUN_COLOR : EARTH_COLOR;
            const right = X(b.az) < PW - 190;
            const label = `${which === "sun" ? "Sun" : "Earth"} ${b.el.toFixed(1)}° · ${
              b.frac >= 0.999 ? "fully visible" : b.frac <= 0.001 ? "hidden" : `${pct(b.frac)} of disc`
            }`;
            return (
              <g key={which} pointerEvents="none">
                <circle cx={X(b.az)} cy={Y(b.el)} r={7} fill={b.visible ? color : "#1c2127"} stroke={INK} strokeWidth={2} />
                <text
                  x={X(b.az) + (right ? 12 : -12)}
                  y={Y(b.el) + (which === "sun" ? -10 : 16)}
                  fill={INK}
                  fontSize={12}
                  textAnchor={right ? "start" : "end"}
                  style={{ paintOrder: "stroke", stroke: "#1c2127", strokeWidth: 4 }}
                >
                  {label}
                </text>
              </g>
            );
          })}
      </svg>
      <div style={{ color: INK_MUTED, fontSize: 12, minHeight: 18, marginTop: 2 }}>
        {cur ? `${fmtUtc(cur.time_utc)} UTC` : "Hover a track or the timeline to inspect one instant."}
      </div>
    </figure>
  );
}

function Legend() {
  const dot = (fill: string, stroke: string) => (
    <svg width={12} height={12} aria-hidden>
      <circle cx={6} cy={6} r={4} fill={fill} stroke={stroke} strokeWidth={1.5} />
    </svg>
  );
  const item = { display: "inline-flex", gap: 5, alignItems: "center" } as const;
  return (
    <span style={{ display: "inline-flex", gap: 12, fontSize: 12, color: INK_MUTED, flexWrap: "wrap" }}>
      <span style={item}>{dot(SUN_COLOR, SUN_COLOR)} Sun</span>
      <span style={item}>{dot(EARTH_COLOR, EARTH_COLOR)} Earth</span>
      <span style={item}>{dot("#1c2127", INK_MUTED)} hollow = hidden by terrain</span>
    </span>
  );
}

/* ------------------------------------------------------------------ timeline */

const TW = 920;
const TP = { l: 96, r: 14, t: 8, b: 26 };
const ROW_H = 62;
const ROW_GAP = 26;

export function VisibilityTimeline({ data, cursor, setCursor }: { data: SitePayload } & CursorProps) {
  const thr = thresholds(data);
  const n = data.sky.length;
  const plotW = TW - TP.l - TP.r;
  const TH = TP.t + 2 * ROW_H + ROW_GAP + TP.b;
  const X = (i: number) => TP.l + (n > 1 ? (i / (n - 1)) * plotW : plotW / 2);
  const tipRef = useRef<HTMLDivElement>(null);
  const [tipX, setTipX] = useState(0);

  const rows = [
    {
      key: "sun",
      title: "Sun",
      sub: "visible disc",
      color: SUN_COLOR,
      frac: data.series.sun_fraction,
      thr: thr.sun,
      gapName: "longest night",
    },
    {
      key: "earth",
      title: "Earth",
      sub: "visible disc",
      color: EARTH_COLOR,
      frac: data.series.earth_fraction,
      thr: thr.earth,
      gapName: "longest no-Earth",
    },
  ];

  // Tick on round hours; samples are `step_min` apart (D-20261117-pj-91c6), so a tick every k hours is every k·60/step samples.
  const stepH = (data.series.step_min ?? 60) / 60;
  const spH = Math.max(1, Math.round(1 / stepH));
  const tickHours = [1, 2, 3, 6, 12, 24, 48, 72, 168].find((k) => ((n - 1) * stepH) / k <= 9) ?? 168;
  const tickEvery = tickHours * spH;
  const hoursText = (samples: number) => String(Number((samples * stepH).toFixed(2)));

  function onMove(ev: MouseEvent<SVGSVGElement>) {
    const x = svgX(ev, TW);
    if (n < 1) return;
    const i = Math.round(((x - TP.l) / plotW) * (n - 1));
    const clamped = Math.min(n - 1, Math.max(0, i));
    setCursor(clamped);
    const r = ev.currentTarget.getBoundingClientRect();
    setTipX((X(clamped) / TW) * r.width);
  }

  return (
    <figure style={{ margin: 0, position: "relative" }}>
      <figcaption style={{ display: "flex", gap: 16, alignItems: "baseline", flexWrap: "wrap", marginBottom: 4 }}>
        <strong>Visibility over the window</strong>
        <span style={{ color: INK_MUTED, fontSize: 12 }}>
          Share of each disc above the terrain, sample by sample. Marked spans are the longest gaps the score uses.
        </span>
      </figcaption>
      <svg
        viewBox={`0 0 ${TW} ${TH}`}
        width="100%"
        role="img"
        aria-label="Visible fraction of the Sun and Earth discs over the time window"
        style={{ display: "block", background: "#1c2127", borderRadius: 4, maxHeight: "17vh" }}
        onMouseMove={onMove}
        onMouseLeave={() => setCursor(null)}
      >
        {rows.map((row, ri) => {
          const y0 = TP.t + ri * (ROW_H + ROW_GAP) + 14;
          const h = ROW_H - 14;
          const Y = (v: number) => y0 + h - Math.min(1, Math.max(0, v)) * h;
          const area =
            `M ${X(0)},${Y(0)} ` +
            row.frac.map((v, i) => `L ${X(i).toFixed(1)},${Y(v).toFixed(1)}`).join(" ") +
            ` L ${X(n - 1)},${Y(0)} Z`;
          const line = row.frac.map((v, i) => `${i ? "L" : "M"} ${X(i).toFixed(1)},${Y(v).toFixed(1)}`).join(" ");
          const [gs, gl] = longestRun(row.frac.map((v) => v <= row.thr));
          const half = n > 1 ? plotW / (n - 1) / 2 : 0;
          const gx0 = Math.max(TP.l, X(gs) - half);
          const gx1 = Math.min(TW - TP.r, X(gs + gl - 1) + half);
          return (
            <g key={row.key}>
              <text x={8} y={y0 + 10} fill={INK} fontSize={12} fontWeight={600}>
                {row.title}
              </text>
              <text x={8} y={y0 + 24} fill={INK_MUTED} fontSize={FONT}>
                {row.sub}
              </text>
              {[0, 1].map((v) => (
                <g key={v}>
                  <line x1={TP.l} x2={TW - TP.r} y1={Y(v)} y2={Y(v)} stroke={GRID} strokeWidth={0.6} />
                  <text x={TP.l - 6} y={Y(v)} fill={INK_MUTED} fontSize={FONT - 1} textAnchor="end" dominantBaseline="middle">
                    {v ? "100 %" : "0 %"}
                  </text>
                </g>
              ))}
              {gl > 0 && (
                <g>
                  <rect x={gx0} y={y0 - 2} width={Math.max(2, gx1 - gx0)} height={h + 4} fill="#000" opacity={0.35} />
                  <line x1={gx0} x2={gx1} y1={y0 - 5} y2={y0 - 5} stroke={INK_MUTED} strokeWidth={1.5} />
                  <text
                    x={Math.min(TW - TP.r - 4, Math.max(TP.l + 4, (gx0 + gx1) / 2))}
                    y={y0 - 9}
                    fill={INK}
                    fontSize={FONT}
                    textAnchor={(gx0 + gx1) / 2 > TW - 140 ? "end" : (gx0 + gx1) / 2 < TP.l + 80 ? "start" : "middle"}
                  >
                    {row.gapName} · {hoursText(gl)} h
                  </text>
                </g>
              )}
              <path d={area} fill={row.color} opacity={0.3} />
              <path d={line} fill="none" stroke={row.color} strokeWidth={2} strokeLinejoin="round" />
              {row.thr > 0 && (
                <g>
                  <line
                    x1={TP.l}
                    x2={TW - TP.r}
                    y1={Y(row.thr)}
                    y2={Y(row.thr)}
                    stroke={INK_MUTED}
                    strokeWidth={1}
                    strokeDasharray="4 4"
                  />
                  <text x={TW - TP.r - 4} y={Y(row.thr) - 4} fill={INK_MUTED} fontSize={FONT - 1} textAnchor="end">
                    need &gt; {pct(row.thr)}
                  </text>
                </g>
              )}
            </g>
          );
        })}
        {data.sky.map((s, i) => {
          if (i % tickEvery !== 0) return null;
          const midnight = s.time_utc.slice(11, 16) === "00:00";
          const label = i === 0 || midnight ? `${s.time_utc.slice(5, 10)} ${s.time_utc.slice(11, 16)}` : s.time_utc.slice(11, 16);
          return (
            <text
              key={i}
              x={X(i)}
              y={TH - 8}
              fill={midnight || i === 0 ? INK : INK_MUTED}
              fontSize={FONT}
              textAnchor={i === 0 ? "start" : X(i) > TW - 40 ? "end" : "middle"}
            >
              {label}
            </text>
          );
        })}
        {cursor != null && (
          <line x1={X(cursor)} x2={X(cursor)} y1={TP.t} y2={TH - TP.b + 4} stroke={INK} strokeWidth={1} pointerEvents="none" />
        )}
      </svg>
      {cursor != null && data.sky[cursor] && (
        <div
          ref={tipRef}
          style={{
            position: "absolute",
            top: 26,
            left: tipX,
            transform: tipX > 600 ? "translateX(calc(-100% - 10px))" : "translateX(10px)",
            background: "#252a31",
            border: "1px solid #5f6b7c",
            borderRadius: 4,
            padding: "6px 8px",
            fontSize: 12,
            pointerEvents: "none",
            whiteSpace: "nowrap",
            color: INK,
          }}
        >
          <div style={{ color: INK_MUTED }}>{fmtUtc(data.sky[cursor].time_utc)} UTC</div>
          <TipRow color={SUN_COLOR} name="Sun" frac={data.series.sun_fraction[cursor]} ok={data.series.sun_fraction[cursor] > thr.sun} />
          <TipRow color={EARTH_COLOR} name="Earth" frac={data.series.earth_fraction[cursor]} ok={data.series.earth_fraction[cursor] > thr.earth} />
        </div>
      )}
      <div style={{ color: INK_MUTED, fontSize: 12, marginTop: 2 }}>Time, UTC</div>
    </figure>
  );
}

function TipRow({ color, name, frac, ok }: { color: string; name: string; frac: number; ok: boolean }) {
  return (
    <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
      <span style={{ width: 10, height: 10, borderRadius: 5, background: color, flex: "none" }} />
      <span style={{ width: 38 }}>{name}</span>
      <strong style={{ fontVariantNumeric: "tabular-nums", width: 44, textAlign: "right" }}>{pct(frac)}</strong>
      <span style={{ color: INK_MUTED }}>{ok ? "counts as visible" : "counts as hidden"}</span>
    </div>
  );
}

/* ------------------------------------------------------- score + needs block */

const FAILING_LABEL: Record<string, string> = {
  night: "the night is not shorter than the limit",
  no_earth: "the gap without Earth is not shorter than the limit",
  battery: "the battery falls below the reserve",
  lit: "continuous sunlight is shorter than required",
  lit_total: "total sunlight is less than required",
  both: "Sun and Earth are never visible together",
  temperature: "the temperature is not below the maximum",
  temperature_min: "the temperature falls below the minimum",
  dust: "soil resistance below the limit",
};

export function ScoreSummary({ data }: { data: SitePayload }) {
  const sc = data.score;
  const s = data.series;
  const needs = data.needs ?? {};
  const failing = sc.breakdown?.failing ?? [];
  const scoreShown = sc.feasible ? sc.score : 0;

  const maxNight = Number(needs.max_night_h);
  const maxNoEarth = Number(needs.max_no_earth_h);
  const minLit = Number(needs.min_continuous_lit_h ?? 0);
  const minTotalLit = Number(needs.min_total_lit_h ?? 0);
  const energyMode = Boolean(needs.energy_mode) && s.soc_min != null;

  // Surface-hazard rows appear only when a limit is active; a limit listed in needs.not_evaluated is shown
  // as "not evaluated" with the reason, never as a pass or a fail (D-20261118-pj-b3dc).
  const agg = (data.hazards as { aggregate?: Record<string, number | null> } | undefined)?.aggregate;
  const notEval = new Set(data.needs?.not_evaluated ?? []);
  const unavailable = data.hazards_status?.unavailable ?? {};
  const why = (limit: string) => reasonShort(unavailable[limit === "min_soil_resistance" ? "soil_resistance" : "temperature"]);
  const hazRows: React.ComponentProps<typeof NeedRow>[] = [];
  const tMin = agg ? (agg.temperature_min_k ?? agg.temperature_k) : null;
  if (needs.max_temperature_k != null) {
    if (notEval.has("max_temperature_k"))
      hazRows.push({ label: "Peak temperature", actual: 0, limit: Number(needs.max_temperature_k), kind: "max", unit: "K", failed: false, notEvaluated: why("max_temperature_k") });
    else if (agg && agg.temperature_k != null)
      hazRows.push({ label: "Peak temperature", actual: Math.round(agg.temperature_k), limit: Number(needs.max_temperature_k), kind: "max", unit: "K", failed: failing.includes("temperature") });
  }
  if (needs.min_temperature_k != null) {
    if (notEval.has("min_temperature_k"))
      hazRows.push({ label: "Coldest temperature", actual: 0, limit: Number(needs.min_temperature_k), kind: "min", unit: "K", failed: false, notEvaluated: why("min_temperature_k") });
    else if (agg && tMin != null)
      hazRows.push({ label: "Coldest temperature", actual: Math.round(tMin), limit: Number(needs.min_temperature_k), kind: "min", unit: "K", failed: failing.includes("temperature_min") });
  }
  if (needs.min_soil_resistance != null) {
    if (notEval.has("min_soil_resistance"))
      hazRows.push({ label: "Soil resistance", actual: 0, limit: Number(needs.min_soil_resistance), kind: "min", unit: "J/m³", digits: 2, failed: false, notEvaluated: why("min_soil_resistance") });
    else if (agg && agg.soil_resistance != null)
      hazRows.push({ label: "Soil resistance", actual: agg.soil_resistance, limit: Number(needs.min_soil_resistance), kind: "min", unit: "J/m³", digits: 2, failed: failing.includes("dust") });
  }

  return (
    <div style={{ display: "grid", gridTemplateColumns: "minmax(200px, 260px) 1fr", gap: 24, alignItems: "start" }}>
      <section aria-label="Score">
        <div style={{ color: INK_MUTED, fontSize: 12 }}>Score for this site and window</div>
        <div style={{ display: "flex", alignItems: "baseline", gap: 10, margin: "2px 0 4px" }}>
          <span style={{ fontSize: 22, lineHeight: 1.2, fontWeight: 500, color: INK, fontFamily: MONO, fontVariantNumeric: "tabular-nums" }}>
            {scoreShown.toFixed(2)}
          </span>
          <Tag minimal intent={sc.feasible ? "success" : "danger"} style={{ textTransform: "uppercase", letterSpacing: "0.04em", fontSize: 11 }}>
            {sc.feasible ? "Feasible" : "Infeasible"}
          </Tag>
        </div>
        <div style={{ fontSize: 11, color: INK_MUTED }}>
          Absolute scale 0 – {SCORE_CEILING}+ (higher is better)
        </div>
        <div style={{ fontSize: 11, color: INK_MUTED }}>Ranking index, not a probability of success.</div>
        {!sc.feasible && (
          <p style={{ margin: "6px 0 0", fontSize: 12, color: INK_MUTED }}>
            {failing.length
              ? `Fails because ${failing.map((f) => FAILING_LABEL[f] ?? f).join("; ")}.`
              : "At least one mission need is not met."}
            {sc.companion_score != null && ` Companion score for ranking: ${sc.companion_score.toFixed(2)}.`}
          </p>
        )}
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginTop: 8 }}>
          <Tag minimal icon={s.any_both ? "tick" : "cross"} intent={needs.require_both && !s.any_both ? "danger" : "none"}>
            Sun + Earth together: {s.any_both ? "yes" : "never"}
            {needs.require_both ? " (required)" : ""}
          </Tag>
          <Tag minimal>Hazards: {data.hazards_enabled ? "on" : "off"}</Tag>
        </div>
      </section>

      <section aria-label="Mission needs versus this site and window">
        <HTMLTable compact style={{ width: "100%" }}>
          <thead>
            <tr>
              <th>Need</th>
              <th style={{ textAlign: "right" }}>Actual</th>
              <th style={{ textAlign: "right" }}>Limit</th>
              <th style={{ width: "34%" }} aria-label="Actual against limit" />
              <th aria-label="Status" />
            </tr>
          </thead>
          <tbody>
            {energyMode ? (
              <NeedRow label="Lowest battery" actual={Math.round((s.soc_min ?? 1) * 100)} limit={Math.round(Number(needs.reserve_pct ?? 10))} kind="min" unit="%" failed={failing.includes("battery")} />
            ) : (
              <NeedRow label="Longest night" actual={s.longest_night_h} limit={maxNight} kind="max" failed={failing.includes("night")} />
            )}
            <NeedRow label="Longest gap without Earth" actual={s.longest_no_earth_h} limit={maxNoEarth} kind="max" failed={failing.includes("no_earth")} />
            <NeedRow label="Longest continuous sunlight" actual={s.longest_lit_h ?? 0} limit={minLit} kind="min" failed={failing.includes("lit")} />
            {minTotalLit > 0 && (
              <NeedRow label="Total sunlight" actual={s.hours_sun_above_threshold ?? 0} limit={minTotalLit} kind="min" failed={failing.includes("lit_total")} />
            )}
            {hazRows.map((r) => (
              <NeedRow key={r.label} {...r} />
            ))}
          </tbody>
        </HTMLTable>
      </section>
    </div>
  );
}

/** Short (2-3 word) reason a limit could not be checked, from the backend's reason text. */
export function reasonShort(reason: string | undefined): string {
  const r = (reason ?? "").toLowerCase().trim();
  if (!r) return "data missing";
  if (r === "temperature data missing" || r === "slope data missing") return "data missing";
  if (r === "temperature bin missing") return "bin missing";
  if (r === "outside temperature map" || r === "outside slope map") return "outside map";
  if (r === "season not computable") return "season unknown";
  return r.split(/\s+/).slice(0, 3).join(" ");
}

/** One row of the needs table: neutral bar, limit tick; colour only when the need fails (D-20261117-pj-f19a). */
function NeedRow({
  label,
  actual,
  limit,
  kind,
  failed,
  unit = "h",
  digits = 0,
  notEvaluated,
}: {
  label: string;
  actual: number;
  limit: number;
  kind: "max" | "min";
  failed: boolean;
  unit?: string;
  digits?: number;
  /** Short reason; set when this limit could not be checked (neither pass nor fail). */
  notEvaluated?: string;
}) {
  const hasLimit = Number.isFinite(limit) && (unit === "h" ? limit > 0 : true);
  // A maximum fails when equal (D-20261118-pj-9413): it must stay strictly below the limit.
  const ok = !failed && (!hasLimit || (kind === "max" ? actual < limit : actual >= limit));
  if (notEvaluated) {
    return (
      <tr>
        <td>{label}</td>
        <td colSpan={2} style={{ textAlign: "right", color: INK_MUTED }}>
          <span title={notEvaluated}>not evaluated</span>
          <span style={{ fontFamily: MONO, fontVariantNumeric: "tabular-nums" }}>
            {" · "}
            {kind === "max" ? "less than" : "at least"} {limit} {unit}
          </span>
        </td>
        <td style={{ color: INK_MUTED, fontSize: 12 }}>{notEvaluated}</td>
        <td>
          <Icon icon="help" size={14} color={INK_MUTED} title={`Not evaluated: ${notEvaluated}`} />
        </td>
      </tr>
    );
  }
  const scale = Math.max(actual, hasLimit ? limit : 0, 1) * 1.15;
  return (
    <tr>
      <td>{label}</td>
      <td style={{ textAlign: "right", fontFamily: MONO, fontVariantNumeric: "tabular-nums" }}>{Number(actual.toFixed(digits === 0 ? 3 : digits))} {unit}</td>
      <td style={{ textAlign: "right", fontFamily: MONO, fontVariantNumeric: "tabular-nums", color: INK_MUTED }}>
        {hasLimit ? `${kind === "max" ? "less than" : "at least"} ${limit} ${unit}` : "none"}
      </td>
      <td>
        <div style={{ position: "relative", height: 6, background: "#2f343c", borderRadius: 2 }}>
          <div
            style={{
              width: `${Math.min(100, (actual / scale) * 100)}%`,
              height: "100%",
              background: ok ? "#8f99a8" : BAD_COLOR,
              borderRadius: 2,
              minWidth: actual > 0 ? 3 : 0,
            }}
          />
          {hasLimit && (
            <span
              title={`${kind === "max" ? "Must be less than" : "At least"}: ${limit} ${unit}`}
              style={{ position: "absolute", left: `${(limit / scale) * 100}%`, top: -3, width: 2, height: 12, background: INK }}
            />
          )}
        </div>
      </td>
      <td>
        <Icon icon={ok ? "tick" : "error"} size={14} color={ok ? INK_MUTED : BAD_COLOR} title={ok ? "Need met" : "Need not met"} />
      </td>
    </tr>
  );
}

/* --------------------------------------------------------------- composite */

/** ONE compact warning line (click to expand), instead of a stack of disclaimers. */
function WarningLine({ warnings }: { warnings: NonNullable<SitePayload["warnings"]> }) {
  const [open, setOpen] = useState(false);
  const text = warnings.map((w) => w.message).join(" ");
  return (
    <Callout intent="warning" icon="warning-sign" style={{ padding: "6px 10px" }}>
      <div
        role="button"
        tabIndex={0}
        title={open ? "Click to collapse" : text}
        onClick={() => setOpen((o) => !o)}
        onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && setOpen((o) => !o)}
        style={{ cursor: "pointer", fontSize: 12, ...(open ? {} : { whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }) }}
      >
        {text}
      </div>
    </Callout>
  );
}

export function SiteResult({ data }: { data: SitePayload }) {
  const [cursor, setCursor] = useState<number | null>(null);
  return (
    <div style={{ display: "grid", gap: 14 }}>
      {data.warnings && data.warnings.length > 0 && <WarningLine warnings={data.warnings} />}
      <ScoreSummary data={data} />
      <HorizonPanorama data={data} cursor={cursor} setCursor={setCursor} />
      <VisibilityTimeline data={data} cursor={cursor} setCursor={setCursor} />
    </div>
  );
}

