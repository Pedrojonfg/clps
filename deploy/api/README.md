# Hosted API (no personal machine needed)

The desktop app calls the evaluator API at `https://api.pedrojon.com`. This folder runs it on any
Linux VPS with Docker. Heavy site×time work happens here; masks come from the R2 store
(`masks.pedrojon.com`) and are cached on the server.

## One-time setup on the VPS

1. DNS (Cloudflare): `A  api  →  <VPS IP>`, proxy **off** (grey cloud) so Caddy can get its own certificate.
2. Open ports 80 and 443 in the VPS firewall / cloud security list.
3. Copy the non-mask data once (about 2.5 GB), from the machine that has it:

```bash
rsync -avP data/kernels                          user@VPS:~/clps/deploy/api/data/
rsync -avP data/hazards/pcp/summer data/hazards/pcp/winter  user@VPS:~/clps/deploy/api/data/hazards/pcp/
rsync -avP data/dem/LDSM_80S_80MPP_ADJ.TIF data/dem/LPSR_80S_20MPP_ADJ.TIF  user@VPS:~/clps/deploy/api/data/dem/
```

   Create the target folders first (`mkdir -p deploy/api/data/hazards/pcp deploy/api/data/dem`).

4. Start it:

```bash
git clone https://github.com/Pedrojonfg/clps && cd clps/deploy/api
docker compose up -d --build
curl https://api.pedrojon.com/health
```

## Sizing

Masks are not stored here (R2 cache, about 0.9 GB at most). A 2 vCPU / 4 GB VPS handles single-site
evaluations comfortably; deep searches over big rectangles are the heavy path, so keep an eye on CPU.
There is no auth or rate limit yet: anyone with the URL can call it.

## Update

```bash
git pull && docker compose up -d --build
```
