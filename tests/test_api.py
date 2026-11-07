"""API tests with the pipeline and NLI model mocked: no Groq calls, no model download."""

import time

import pytest
from fastapi.testclient import TestClient

from licensewise import api, pipeline, verifier

RESULT = {"input": {"description": "d", "manifest": None},
          "recommendations": [{"spdx_id": "MIT", "claims": [{"status": "verified"}, {"status": "unverified"}]}]}


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(api, "RUNS", tmp_path)
    monkeypatch.setattr(api, "DB", tmp_path / "test.db")
    monkeypatch.setattr(api, "LEGACY_JSON", tmp_path / "api")
    monkeypatch.setattr(verifier, "load", lambda: None)
    calls = []

    def fake_recommend(description, manifest, verify=True, progress=None):
        calls.append(description)
        for step in ("dependencies", "stage1", "response"):
            progress(step)
        if description == "boom":
            raise RuntimeError("Error code: 429 rate_limit_exceeded")
        return {**RESULT, "input": {"description": description, "manifest": None}}

    monkeypatch.setattr(pipeline, "recommend", fake_recommend)
    with TestClient(api.app) as c:
        c.calls = calls
        yield c


def wait(client, job_id):
    for _ in range(100):
        job = client.get(f"/api/recommendations/{job_id}").json()
        if job["status"] in ("done", "failed"):
            return job
        time.sleep(0.02)
    raise AssertionError("job did not finish")


def test_health_and_licenses(client):
    assert client.get("/api/health").json()["steps"][0] == "input"
    licenses = client.get("/api/licenses").json()
    mit = next(l for l in licenses if l["spdx_id"] == "MIT")
    assert mit["copyleft"] == "none"


def test_run_reuse_and_history(client):
    r = client.post("/api/recommendations", json={"description": "a CLI tool"})
    assert r.status_code == 202 and r.json()["reused"] is False
    job = wait(client, r.json()["id"])
    assert job["status"] == "done" and job["result"]["recommendations"][0]["spdx_id"] == "MIT"
    assert "key" not in job

    again = client.post("/api/recommendations", json={"description": "  a CLI tool "})
    assert again.json()["reused"] is True and again.json()["id"] == job["id"]
    assert client.calls == ["a CLI tool"]  # no second pipeline call

    [summary] = client.get("/api/recommendations").json()
    assert summary["top_pick"] == "MIT" and (summary["claims_verified"], summary["claims_total"]) == (1, 2)


def test_jobs_survive_restart(client):
    job_id = client.post("/api/recommendations", json={"description": "persist me"}).json()["id"]
    wait(client, job_id)
    api._jobs.clear()
    api._load_runs()  # what a restart does
    assert api._jobs[job_id]["status"] == "done"


def test_failure_message_is_friendly(client):
    job = wait(client, client.post("/api/recommendations", json={"description": "boom"}).json()["id"])
    assert job["status"] == "failed" and "free-tier limit" in job["error"]


@pytest.mark.parametrize("body", [
    {},
    {"description": "   "},
    {"manifest": {"name": "package.json", "content": "not json"}},
    {"manifest": {"name": "package.json", "content": "{}"}},
    {"manifest": {"name": "Cargo.toml", "content": ""}},
])
def test_bad_input_is_rejected(client, body):
    assert client.post("/api/recommendations", json=body).status_code == 422


def test_unknown_job(client):
    assert client.get("/api/recommendations/nope").status_code == 404
