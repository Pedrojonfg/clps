import type { SitePayload } from "./types";

const CX = 200;
const CY = 200;
const R_MAX = 168;
const EL_MAX = 8;

function azElevToXY(azDeg: number, elDeg: number) {
  const rad = ((azDeg - 90) * Math.PI) / 180;
  const r = (Math.max(elDeg, 0) / EL_MAX) * R_MAX;
  return { x: CX + r * Math.cos(rad), y: CY + r * Math.sin(rad) };
}

type Props = { data: SitePayload };

export function PolarChart({ data }: Props) {
  const mask = data.mask.elevation_deg;
  const pts: string[] = [];
  for (let i = 0; i < Math.min(mask.length, 720); i++) {
    const p = azElevToXY(i * 0.5, mask[i]);
    pts.push(`${p.x},${p.y}`);
  }
  const origin = azElevToXY(0, 0);
  const pathD = `M ${origin.x},${origin.y} L ${pts.join(" L ")} Z`;

  const sunPts = data.sky
    .map((s) => {
      const p = azElevToXY(s.sun_az_deg, s.sun_el_deg);
      return `${p.x},${p.y}`;
    })
    .join(" ");
  const earthPts = data.sky
    .map((s) => {
      const p = azElevToXY(s.earth_az_deg, s.earth_el_deg);
      return `${p.x},${p.y}`;
    })
    .join(" ");

  const sunThr = Number(data.needs?.sun_lit_threshold ?? 0);
  const earthThr = Number(data.needs?.earth_lit_threshold ?? 0);

  return (
    <div>
      <svg viewBox="0 0 400 400" width="100%" style={{ maxWidth: 440, display: "block" }}>
        {[2, 4, 6, 8].map((el) => (
          <circle
            key={el}
            cx={CX}
            cy={CY}
            r={(el / EL_MAX) * R_MAX}
            fill="none"
            stroke="#3f4556"
            strokeWidth={0.5}
          />
        ))}
        {(["N", "E", "S", "W"] as const).map((lab, i) => {
          const p = azElevToXY([0, 90, 180, 270][i], EL_MAX + 0.6);
          return (
            <text
              key={lab}
              x={p.x}
              y={p.y}
              fill="#abb3bf"
              fontSize={11}
              textAnchor="middle"
              dominantBaseline="middle"
            >
              {lab}
            </text>
          );
        })}
        <path d={pathD} fill="#6b6370" stroke="#c4b8a8" strokeWidth={1.6} opacity={0.95} />
        <polyline
          points={earthPts}
          fill="none"
          stroke="#6a8faa"
          strokeWidth={1.4}
          strokeLinejoin="round"
        />
        <polyline
          points={sunPts}
          fill="none"
          stroke="#c9a227"
          strokeWidth={1.8}
          strokeLinejoin="round"
        />
        {data.sky.map((s, i) => {
          if (i % 3 !== 0) return null;
          const pSun = azElevToXY(s.sun_az_deg, s.sun_el_deg);
          const pEarth = azElevToXY(s.earth_az_deg, s.earth_el_deg);
          return (
            <g key={s.time_utc}>
              <circle cx={pSun.x} cy={pSun.y} r={2.2} fill="#c9a227" />
              <circle cx={pEarth.x} cy={pEarth.y} r={1.6} fill="#6a8faa" />
            </g>
          );
        })}
      </svg>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: `repeat(${data.sky.length}, 1fr)`,
          height: 10,
          marginTop: 8,
          gap: 1,
        }}
      >
        {data.sky.map((s, i) => {
          const sf = data.series.sun_fraction[i] > sunThr;
          const ef = data.series.earth_fraction[i] > earthThr;
          let bg = "#3d3f48";
          if (sf && ef) bg = "#4a6b5c";
          else if (sf) bg = "#c9a227";
          else if (ef) bg = "#6a8faa";
          return <div key={s.time_utc} title={s.time_utc} style={{ background: bg }} />;
        })}
      </div>
      <div style={{ display: "flex", gap: 12, marginTop: 6, fontSize: 12, color: "#abb3bf" }}>
        <span>Sun</span>
        <span>Earth</span>
        <span>Both</span>
        <span>Neither</span>
      </div>
    </div>
  );
}
