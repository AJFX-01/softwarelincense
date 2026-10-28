"""HTTP API for the web UI.

A run takes 1-5 minutes on Groq's free tier, so POST /api/recommendations
returns a job ID at once and the UI polls GET /api/recommendations/{id}.
Jobs run one at a time (Groq's per-minute token limit and the single NLI
model in memory make parallel runs slower, not faster) and are saved as JSON
in data/runs/api/ so history survives a restart. Identical inputs reuse the
finished result instead of spending tokens again.

Run:  .venv/bin/uvicorn licensewise.api:app --port 8000
"""

import hashlib
import json
import tempfile
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from licensewise import ROOT, deps, kb, llm, pipeline, verifier

RUNS = ROOT / "data" / "runs" / "api"
MANIFESTS = ("requirements.txt", "pyproject.toml", "package.json")
MAX_DESCRIPTION = 4000
MAX_MANIFEST_BYTES = 100_000
# Pipeline steps in order; the UI shows the same list.
STEPS = ["input", "dependencies", "stage1", "retrieval", "explain", "verify", "response"]

_jobs: dict[str, dict] = {}
_lock = threading.Lock()
_worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix="pipeline")


class Manifest(BaseModel):
    name: Literal["requirements.txt", "pyproject.toml", "package.json"]
    content: str = Field(max_length=MAX_MANIFEST_BYTES)


class RecommendRequest(BaseModel):
    description: str | None = Field(default=None, max_length=MAX_DESCRIPTION)
    manifest: Manifest | None = None
    verify: bool = True


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _save(job):
    RUNS.mkdir(parents=True, exist_ok=True)
    (RUNS / f"{job['id']}.json").write_text(json.dumps(job, indent=1))


def _update(job_id, **fields):
    with _lock:
        job = _jobs[job_id]
        job.update(fields)
        _save(job)


def _summary(job):
    """Small view of a job for the history list."""
    result = job.get("result") or {}
    claims = [c for r in result.get("recommendations", []) for c in r["claims"]]
    return {
        "id": job["id"], "status": job["status"], "created_at": job["created_at"],
        "description": job["input"]["description"],
        "manifest_name": (job["input"]["manifest"] or {}).get("name"),
        "top_pick": (result.get("recommendations") or [{}])[0].get("spdx_id"),
        "claims_verified": sum(c["status"] == "verified" for c in claims),
        "claims_total": len(claims),
        "error": job.get("error"),
    }


def _load_runs():
    """Read saved jobs; anything left queued or running was cut off by a restart."""
    for path in sorted(RUNS.glob("*.json")):
        job = json.loads(path.read_text())
        if job["status"] in ("queued", "running"):
            job.update(status="failed", error="The server restarted before this run finished.")
            _save(job)
        _jobs[job["id"]] = job


def _run(job_id):
    job = _jobs[job_id]
    _update(job_id, status="running", step="input", step_detail=None, started_at=_now())
    try:
        manifest = job["input"]["manifest"]
        with tempfile.TemporaryDirectory() as tmp:
            path = None
            if manifest:  # deps.py reads a file and dispatches on its name
                path = Path(tmp) / manifest["name"]
                path.write_text(manifest["content"])
            result = pipeline.recommend(
                job["input"]["description"], path, verify=job["input"]["verify"],
                progress=lambda step, detail=None: _update(job_id, step=step, step_detail=detail))
        result["input"]["manifest"] = manifest["name"] if manifest else None
        _update(job_id, status="done", step=None, step_detail=None, result=result,
                finished_at=_now())
    except (Exception, SystemExit) as e:  # llm.client() exits if the API key is missing
        _update(job_id, status="failed", error=_explain_error(e), finished_at=_now())


def _explain_error(e):
    text = str(e)
    if "rate_limit" in text or "429" in text:
        return "Groq's free-tier limit was reached. Wait a few minutes (or until tomorrow for the daily limit) and try again."
    if "GROQ_API_KEY" in text:
        return "The server has no GROQ_API_KEY. Add it to .env at the project root and restart."
    return f"{type(e).__name__}: {text[:300]}"


@asynccontextmanager
async def lifespan(_app):
    _load_runs()
    _worker.submit(verifier.load)  # queued ahead of any job, so the first run is not slower
    yield
    _worker.shutdown(wait=False, cancel_futures=True)


app = FastAPI(title="LicenseWise API", version="1.0", lifespan=lifespan)


@app.get("/api/health")
def health():
    return {"status": "ok", "model": llm.PIPELINE_MODEL, "nli_model": verifier.NLI_MODEL,
            "steps": STEPS}


@app.get("/api/licenses")
def licenses():
    fields = ("spdx_id", "title", "nickname", "description", "permissions", "conditions",
              "limitations", "language")
    return [{**{f: lic[f] for f in fields}, "copyleft": kb.copyleft(lic)}
            for _, lic in sorted(kb.licenses().items())]


@app.post("/api/recommendations", status_code=202)
def create(request: RecommendRequest):
    description = (request.description or "").strip() or None
    manifest = request.manifest.model_dump() if request.manifest else None
    if not description and not manifest:
        raise HTTPException(422, "Add a project description, a manifest, or both.")
    if manifest:
        _check_manifest(manifest)

    key = hashlib.sha256(json.dumps([llm.PIPELINE_MODEL, description, manifest, request.verify])
                         .encode()).hexdigest()
    with _lock:
        for job in _jobs.values():  # same input already done or in progress
            if job["key"] == key and job["status"] != "failed":
                return {**_summary(job), "reused": True}
        job = {"id": uuid.uuid4().hex[:12], "key": key, "status": "queued", "step": None,
               "step_detail": None, "created_at": _now(), "error": None, "result": None,
               "input": {"description": description, "manifest": manifest,
                         "verify": request.verify}}
        _jobs[job["id"]] = job
        _save(job)
    _worker.submit(_run, job["id"])
    return {**_summary(job), "reused": False}


def _check_manifest(manifest):
    """Parse it now so a bad file fails here, not minutes later in the worker."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / manifest["name"]
        path.write_text(manifest["content"])
        try:
            _, names = deps.parse_manifest(path)
        except Exception:
            raise HTTPException(422, f"Could not parse {manifest['name']}. Check that it is valid.")
    if not names:
        raise HTTPException(422, f"No dependencies found in {manifest['name']}.")


@app.get("/api/recommendations")
def history(limit: int = 50):
    with _lock:
        jobs = sorted(_jobs.values(), key=lambda j: j["created_at"], reverse=True)[:limit]
        return [_summary(j) for j in jobs]


@app.get("/api/recommendations/{job_id}")
def get(job_id: str):
    with _lock:
        job = _jobs.get(job_id)
        if not job:
            raise HTTPException(404, "No run with this ID.")
        queued_ahead = sum(j["status"] == "queued" and j["created_at"] < job["created_at"]
                           for j in _jobs.values()) if job["status"] == "queued" else 0
        return {**{k: v for k, v in job.items() if k != "key"}, "queued_ahead": queued_ahead}
