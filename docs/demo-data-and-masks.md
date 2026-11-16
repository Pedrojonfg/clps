# Demo data and horizon masks

Honest claims for the **portfolio static demo** (`D-a988`). This is presentation wording, not a certification.

## What the live demo uses

| Layer | This tranche | Claim |
|-------|------------|-------|
| **Mask time series in the browser** | **Mocked** client-side (`D-3832`, `D-4494`) | Do **not** say there is a live mask API or server-backed mask fetch on GitHub Pages. |
| **Ephemeris / scoring in the demo** | Mostly client or baked UI state per page | Evaluator logic runs **on the client** in the product direction; remote role is store/serve **masks** later (`D-8c03`). |

There is **no mask API contract** in this tranche (`D-3832`). Product intent: masks eventually from a **server API** (shape TBD).

## What was actually computed (offline)

An overnight **1 km spacing** cap precompute finished on disk:

- Path: `data/masks/cap_1km/` (tiles + `summary.json`)
- Scale: on the order of **~290k** horizon masks (~839 MB total — see cap run summary in repo records)

You **may** describe that dataset as **computed** (real precompute output from `scripts/precompute.py`). It is **not** automatically what every point in the public demo shows.

## What is mocked vs computed in the UI

Per `D-a988`:

- **Computed (claim OK):** masks in the overnight **1 km cap** archive on disk (`data/masks/cap_1km`).
- **Mocked (must say so):** mask series **shown in the live demo** outside that backed set — demo uses mocks for delivery (`D-3832`).
- **Planned, not done:** full-cap precompute (e.g. **100 m** spacing) as the **application basis**; **where** the full mask archive will be published is **deferred** (URL/path TBD).

**Wrong claims:** calling mocked demo curves “computed”; implying the full 100 m cap exists; implying a live mask server is running on Pages.

## Out of scope for this tranche

- **100 m** precompute, Hetzner benchmark, and dedicated mask **serving** host — **starts after** this tranche (`D-573b`, `D-8c03`).
- **Deploy:** static GitHub Pages only — see [deploy/README.md](../deploy/README.md) (`D-2533`, `D-c30e`).

## Decision index

| ID | Topic |
|----|--------|
| `D-a988` | Computed vs mocked vs full-cap plan |
| `D-3832` | Mocks now; API later |
| `D-4494` | This tranche = deploy docs; mask API out |
| `D-8c03` | Product: remote masks; client evaluator |
| `D-573b` | 100 m + server work after this tranche |