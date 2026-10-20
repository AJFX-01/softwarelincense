# LicenseWise UI (demo)

React + Vite + TypeScript front end for the v1 pipeline. **Not connected to a backend yet**:
every screen uses real outputs saved from `scripts/recommend.py` (`src/mock/`).

```bash
cd ui
pnpm install
pnpm dev             # http://localhost:5173
```

Demo shortcuts: `/?example=saas`, `/?example=clinic` (opens a result), `/?page=licenses`, `/?page=pipeline`.

Screens: New recommendation (describe / upload manifest, simulated pipeline progress, results with
verified / unverified / contradicted claims and an evidence drawer) · History · License catalogue · Pipeline & evaluation.

To connect the backend later, replace the mock in `src/pages/NewRecommendation.tsx` (`run()`) with
`POST /recommend` → poll `GET /jobs/{id}`; the response shape is `src/types.ts` (`Result`).
