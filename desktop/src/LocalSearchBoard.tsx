/**
 * Local-search (time slide) leaderboard: a strip of every evaluated start plus the ranked
 * table. Order is the API's (D-9cc5 / D-72bc / D-5577); mock rows are tagged (D-20261116-pj-4902).
 */
import { useMemo, useState } from "react";
import { Button, Checkbox, Classes, HTMLTable, Icon, Tag } from "@blueprintjs/core";
import { GRID, INK, INK_MUTED, MONO, fmtUtc } from "./lib/sky";
import type { SitePayload } from "./types";

const SCORE_CEILING = 1.4;
const FEASIBLE = "#8abbff";
const INFEASIBLE = "#b083f0"; // same violet as the region map (D-20261116-pj-2325)
const TOP_N = 10;
const W = 920;
const H = 132;
const P = { l: 44, r: 14, t: 16, b: 30 };

type Row = NonNullable<SitePayload["local_search"]>["leaderboard"][number];

export function LocalSearchBoard({
  data,
  onUseStart,
}: {
  data: SitePayload;
  onUseStart?: (windowStartIso: string) => void;
}) {
  const ls = data.local_search;
  const [hideGapStars, setHideGapStars] = useState(false);
  const [showAll, setShowAll] = useState(false);
  const [hover, setHover] = useState<number | null>(null);
  const anchor = Date.parse(data.sky[0]?.time_utc ?? "");

  const rows = useMemo(() => {
    const all = ls?.leaderboard ?? [];
    return all.map((r, i) => ({
      ...r,
      rank: i + 1,
      offset: r.window_start ? Math.round((Date.parse(r.window_start) - anchor) / 3_600_000) : 0,
      isPick: Boolean(ls?.pick && r.window_start === ls.pick.window_start && r.distance_km === 0),
    }));
  }, [ls, anchor]);

  if (!ls || rows.length === 0) return null;

  const shown = rows.filter((r) => !hideGapStars || !r.hazard_gap_star);
  const table = showAll ? shown : shown.slice(0, TOP_N);
  const anyKm = rows.some((r) => r.distance_km > 0);
  const byOffset = [...shown].filter((r) => r.distance_km === 0).sort((a, b) => a.offset - b.offset);
  const span = Math.max(1, ...byOffset.map((r) => Math.abs(r.offset)));
  const plotW = W - P.l - P.r;
  const plotH = H - P.t - P.b;
  const X = (off: number) => P.l + ((off + span) / (2 * span)) * plotW;
  const Y = (v: number) => P.t + plotH - (Math.min(SCORE_CEILING, Math.max(0, v)) / SCORE_CEILING) * plotH;
  const barW = Math.max(2, Math.min(14, plotW / (2 * span + 1) - 2));
  const nFeasible = rows.filter((r) => r.feasible).length;
  const hovered = hover != null ? byOffset.find((r) => r.rank === hover) : null;
  const mock = data.data_source !== "real";

  return (
    <section style={{ marginTop: 28 }}>
      <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
        <h3 className={Classes.HEADING} style={{ margin: 0 }}>
          Local search — best nearby starts
        </h3>
        {mock && (
          <Tag minimal intent="warning">
            mock data — not a real search
          </Tag>
        )}
      </div>
      <p className={Classes.TEXT_MUTED} style={{ margin: "4px 0 10px", fontSize: 12 }}>
        Same site, window start slid hour by hour around your start. {rows.length} starts evaluated,{" "}
        {nFeasible} feasible. Feasible starts rank by closeness to your start, then score; infeasible ones follow, by
        companion score.
      </p>

      <div style={{ position: "relative" }}>
        <svg
          viewBox={`0 0 ${W} ${H}`}
          width="100%"
          role="img"
          aria-label="Score of each evaluated window start, by hours from the requested start"
          style={{ display: "block", background: "#1c2127", borderRadius: 4 }}
          onMouseLeave={() => setHover(null)}
        >
          {[0, 0.7, 1.4].map((v) => (
            <g key={v}>
              <line x1={P.l} x2={W - P.r} y1={Y(v)} y2={Y(v)} stroke={GRID} strokeWidth={0.6} />
              <text x={P.l - 6} y={Y(v)} fill={INK_MUTED} fontSize={11} textAnchor="end" dominantBaseline="middle">
                {v}
              </text>
            </g>
          ))}
          {byOffset.map((r) => {
            const v = r.feasible ? r.score : r.companion_score;
            const y = Y(v);
            const active = hover === r.rank;
            return (
              <g key={r.rank} onMouseEnter={() => setHover(r.rank)}>
                <rect x={X(r.offset) - barW / 2 - 1} y={P.t} width={barW + 2} height={plotH} fill="transparent" />
                <rect
                  x={X(r.offset) - barW / 2}
                  y={y}
                  width={barW}
                  height={Math.max(2, P.t + plotH - y)}
                  rx={1.5}
                  fill={r.feasible ? FEASIBLE : "none"}
                  stroke={r.feasible ? (active || r.isPick ? INK : "none") : INFEASIBLE}
                  strokeWidth={r.feasible ? (active || r.isPick ? 1.5 : 0) : 1.5}
                  strokeDasharray={r.feasible ? undefined : "3 2"}
                  opacity={r.feasible ? 1 : active ? 1 : 0.85}
                />
                {r.isPick && (
                  <text x={X(r.offset)} y={y - 5} fill={INK} fontSize={11} textAnchor="middle">
                    ★ pick
                  </text>
                )}
              </g>
            );
          })}
          {[-span, -Math.round(span / 2), 0, Math.round(span / 2), span].map((off) => (
            <text key={off} x={X(off)} y={H - 10} fill={off === 0 ? INK : INK_MUTED} fontSize={11} textAnchor="middle">
              {off === 0 ? "your start" : `${off > 0 ? "+" : "−"}${Math.abs(off)} h`}
            </text>
          ))}
        </svg>
        {hovered && (
          <div
            style={{
              position: "absolute",
              top: 6,
              left: `${(X(hovered.offset) / W) * 100}%`,
              transform: hovered.offset > 0 ? "translateX(calc(-100% - 12px))" : "translateX(12px)",
              background: "#252a31",
              border: "1px solid #5f6b7c",
              borderRadius: 4,
              padding: "6px 8px",
              fontSize: 12,
              pointerEvents: "none",
              whiteSpace: "nowrap",
            }}
          >
            <div style={{ color: INK_MUTED }}>
              #{hovered.rank} · {hovered.window_start ? fmtUtc(hovered.window_start) : "—"} UTC
            </div>
            <div>
              {hovered.feasible ? (
                <>
                  Score <strong>{hovered.score.toFixed(3)}</strong>
                </>
              ) : (
                <>
                  Infeasible · companion <strong>{hovered.companion_score.toFixed(3)}</strong>
                </>
              )}
            </div>
          </div>
        )}
      </div>
      <div style={{ display: "flex", gap: 14, fontSize: 12, color: INK_MUTED, margin: "4px 0 12px", flexWrap: "wrap" }}>
        <span style={{ display: "inline-flex", gap: 5, alignItems: "center" }}>
          <svg width={10} height={12} aria-hidden>
            <rect x={1} y={1} width={8} height={10} rx={1.5} fill={FEASIBLE} />
          </svg>
          Feasible — score
        </span>
        <span style={{ display: "inline-flex", gap: 5, alignItems: "center" }}>
          <svg width={10} height={12} aria-hidden>
            <rect x={1} y={1} width={8} height={10} rx={1.5} fill="none" stroke={INFEASIBLE} strokeWidth={1.5} strokeDasharray="3 2" />
          </svg>
          Infeasible — companion score (ranking only)
        </span>
        <span style={{ flex: 1 }} />
        <Checkbox
          checked={hideGapStars}
          label="Hide rows with hazard data gaps (*)"
          onChange={(e) => setHideGapStars(e.currentTarget.checked)}
          style={{ margin: 0 }}
        />
      </div>

      <HTMLTable compact striped style={{ width: "100%" }}>
        <thead>
          <tr>
            <th style={{ width: 64 }}>#</th>
            <th>Window start (UTC)</th>
            <th>From your start</th>
            <th>Feasible</th>
            <th style={{ textAlign: "right" }}>Score</th>
            <th style={{ textAlign: "right" }}>Companion</th>
            {anyKm && <th style={{ textAlign: "right" }}>km away</th>}
            {onUseStart && <th />}
          </tr>
        </thead>
        <tbody>
          {table.map((r: Row & { rank: number; offset: number; isPick: boolean }) => (
            <tr key={`${r.window_start}-${r.distance_km}`} style={r.isPick ? { fontWeight: 600 } : undefined}>
              <td style={{ fontVariantNumeric: "tabular-nums", whiteSpace: "nowrap" }}>
                {r.rank}
                {r.isPick ? " ★" : ""}
                {r.hazard_gap_star ? " *" : ""}
              </td>
              <td style={{ fontVariantNumeric: "tabular-nums" }}>{r.window_start ? fmtUtc(r.window_start) : "—"}</td>
              <td style={{ fontVariantNumeric: "tabular-nums" }}>
                {r.offset === 0 ? "your start" : `${r.offset > 0 ? "+" : "−"}${Math.abs(r.offset)} h`}
              </td>
              <td>
                <span style={{ display: "inline-flex", gap: 5, alignItems: "center" }}>
                  <Icon icon={r.feasible ? "tick" : "cross"} size={12} color={r.feasible ? "#72ca9b" : INFEASIBLE} />
                  {r.feasible ? "yes" : "no"}
                </span>
              </td>
              <td style={{ textAlign: "right", fontFamily: MONO, fontVariantNumeric: "tabular-nums" }}>{Number(r.score).toFixed(3)}</td>
              <td style={{ textAlign: "right", fontFamily: MONO, fontVariantNumeric: "tabular-nums" }}>
                {Number(r.companion_score).toFixed(3)}
              </td>
              {anyKm && (
                <td style={{ textAlign: "right", fontFamily: MONO, fontVariantNumeric: "tabular-nums" }}>
                  {Number(r.distance_km).toFixed(3)}
                </td>
              )}
              {onUseStart && (
                <td style={{ textAlign: "right" }}>
                  {r.window_start && r.offset !== 0 && (
                    <Button small minimal onClick={() => onUseStart(r.window_start as string)}>
                      Use this start
                    </Button>
                  )}
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </HTMLTable>
      <div style={{ display: "flex", gap: 12, alignItems: "center", marginTop: 6, fontSize: 12, color: INK_MUTED }}>
        {shown.length > TOP_N && (
          <Button small minimal icon={showAll ? "chevron-up" : "chevron-down"} onClick={() => setShowAll((v) => !v)}>
            {showAll ? `Show top ${TOP_N}` : `Show all ${shown.length}`}
          </Button>
        )}
        <span>★ pick · * hazard data gap at that start</span>
      </div>
    </section>
  );
}
