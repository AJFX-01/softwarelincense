# LicenseWise UI

React + Vite + TypeScript front end for the v1 pipeline, connected to the FastAPI backend
(`licensewise/api.py`). In development Vite proxies `/api` to `http://localhost:8000`.

```bash
# terminal 1: backend (from the project root; needs GROQ_API_KEY in .env)
.venv/bin/pip install fastapi "uvicorn[standard]"
.venv/bin/uvicorn licensewise.api:app --port 8000

# terminal 2: front end
cd ui
pnpm install
pnpm dev             # http://localhost:5173
```

The topbar shows whether the backend is reachable. The first start loads the DeBERTa verifier
(about 1.7 GB, cached after the first download).

## API

| Method | Path | |
|---|---|---|
| GET | `/api/health` | status, model names, pipeline step keys |
| GET | `/api/licenses` | the 34 in-scope licenses with labels and copyleft class |
| POST | `/api/recommendations` | `{description?, manifest?: {name, content}}` → `202` job summary |
| GET | `/api/recommendations` | history (newest first) |
| GET | `/api/recommendations/{id}` | job with `status`, current `step`, and `result` when done |

Runs take 30 s to 5 min on Groq's free tier, so the UI polls the job every 1.5 s. Jobs run one at
a time, are saved in `data/runs/api/` (gitignored), and an identical input reuses the saved result.
Interactive docs: http://localhost:8000/docs.

## Demo links

`/?example=saas` and `/?example=clinic` open results saved earlier from the real pipeline
(`src/mock/`), which also back the license catalogue when the backend is offline. Add
`&stage=input`, `running` or `evidence` to freeze a screen for screenshots. `/?page=licenses`,
`/?page=pipeline` and `/?page=history` open those pages.
