import { useEffect, useRef, useState } from "react";
import { Check, CircleAlert, FileText, FileUp, LoaderCircle, Play, Sparkles, X } from "lucide-react";
import { EXAMPLES, PIPELINE_STEPS, type Example } from "../mock";
import { ALLOWED_MANIFESTS, parseManifest, validateManifest } from "../lib";
import type { Result } from "../types";
import { api } from "../api";
import { ResultView } from "../components/ResultView";
import { StatusBadge } from "../components/Evidence";

type Tab = "describe" | "manifest";
type Manifest = { name: string; content: string };

export function NewRecommendation({ preset, stage }: { preset: Example | null; stage?: string }) {
  // The parent remounts this page (key) when the preset changes, so state starts from it.
  const [tab, setTab] = useState<Tab>(preset?.manifest ? "manifest" : "describe");
  const [description, setDescription] = useState(preset?.description ?? "");
  const [manifest, setManifest] = useState<Manifest | null>(preset?.manifest ?? null);
  const [error, setError] = useState<string | null>(null);
  const frozen = stage === "input" ? -1 : stage === "running" ? 4 : PIPELINE_STEPS.length;
  const resuming = Boolean(preset?.jobId && !preset.result);
  const [step, setStep] = useState(resuming ? 0 : preset ? frozen : -1); // -1 idle, 0..n-1 running, n done
  const [stepDetail, setStepDetail] = useState<string | null>(null);
  const [result, setResult] = useState<Result | null>(preset && frozen === PIPELINE_STEPS.length ? preset.result : null);
  const [isSample, setIsSample] = useState(Boolean(preset && !preset.jobId)); // saved demo result, not a live run
  const [jobId, setJobId] = useState<string | null>(resuming ? preset!.jobId! : null);
  const fileInput = useRef<HTMLInputElement>(null);

  // Poll the running job; the backend reports which pipeline step it is on.
  useEffect(() => {
    if (!jobId) return;
    let stopped = false;
    const poll = async () => {
      try {
        const job = await api.job(jobId);
        if (stopped) return;
        if (job.status === "done" && job.result) {
          setStep(PIPELINE_STEPS.length);
          setResult(job.result);
          setJobId(null);
          return;
        }
        if (job.status === "failed") {
          setError(job.error ?? "The run failed.");
          setStep(-1);
          setJobId(null);
          return;
        }
        const i = PIPELINE_STEPS.findIndex((s) => s.key === job.step);
        setStep(i < 0 ? 0 : i);
        setStepDetail(job.status === "queued" ? `Waiting for ${job.queued_ahead} earlier run(s)` : job.step_detail);
      } catch (e) {
        if (stopped) return;
        setError((e as Error).message);
        setStep(-1);
        setJobId(null);
        return;
      }
      timer = setTimeout(poll, 1500);
    };
    let timer = setTimeout(poll, 0);
    return () => { stopped = true; clearTimeout(timer); };
  }, [jobId]);

  function loadExample(ex: Example) {
    setDescription(ex.description);
    setManifest(ex.manifest);
    setTab(ex.manifest ? "manifest" : "describe");
    setError(null);
    setResult(null);
    setJobId(null); // stop following any run in progress (it still finishes and shows in History)
    setStep(-1);
  }

  async function onFile(file: File) {
    const problem = validateManifest(file);
    if (problem) return setError(problem);
    const content = await file.text();
    try {
      parseManifest(file.name, content);
    } catch {
      return setError(`Could not parse ${file.name}. Check that it is valid.`);
    }
    setError(null);
    setManifest({ name: file.name, content });
  }

  async function run() {
    if (!description.trim() && !manifest) return setError("Add a project description, a manifest, or both.");
    if (description.length > 4000) return setError("Description is longer than 4,000 characters.");
    setError(null);
    setResult(null);
    setIsSample(false);
    setStepDetail(null);
    setStep(0);
    try {
      const job = await api.recommend(description.trim(), manifest);
      setJobId(job.id); // the effect above polls it (a reused result comes back on the first poll)
    } catch (e) {
      setError((e as Error).message);
      setStep(-1);
    }
  }

  const running = step >= 0 && step < PIPELINE_STEPS.length;
  const packages = manifest ? safeParse(manifest) : [];

  return (
    <div className="page-grid">
      <div className="stack">
        <section className="card">
          <div className="tabs">
            <button className={tab === "describe" ? "tab active" : "tab"} onClick={() => setTab("describe")}>
              <FileText size={16} /> Describe your project
            </button>
            <button className={tab === "manifest" ? "tab active" : "tab"} onClick={() => setTab("manifest")}>
              <FileUp size={16} /> Upload manifest {manifest && <span className="count">1</span>}
            </button>
          </div>

          {tab === "describe" ? (
            <>
              <textarea
                className="textarea"
                rows={6}
                placeholder="e.g. I'm building an analytics library that companies will host as SaaS. Improvements should come back to the community."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
              <div className="hint">{description.length}/4000 · Plain language is fine — no license terms needed.</div>
            </>
          ) : manifest ? (
            <div className="file-card">
              <FileText size={18} />
              <div className="file-meta">
                <div className="mono">{manifest.name}</div>
                <div className="muted small">{packages.length} dependencies: {packages.join(", ")}</div>
              </div>
              <button className="icon-btn" onClick={() => setManifest(null)} aria-label="Remove file"><X size={16} /></button>
            </div>
          ) : (
            <div
              className="dropzone"
              onClick={() => fileInput.current?.click()}
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => { e.preventDefault(); if (e.dataTransfer.files[0]) onFile(e.dataTransfer.files[0]); }}
            >
              <FileUp size={22} />
              <div><b>Drop a manifest</b> or click to browse</div>
              <div className="muted small">{ALLOWED_MANIFESTS.join(" · ")} · max 100 KB · parsed, never executed</div>
              <input ref={fileInput} type="file" hidden accept=".txt,.toml,.json"
                     onChange={(e) => e.target.files?.[0] && onFile(e.target.files[0])} />
            </div>
          )}

          {error && <div className="callout callout-error"><CircleAlert size={16} /> {error}</div>}

          <div className="actions">
            <div className="examples">
              <Sparkles size={15} className="icon-muted" />
              {EXAMPLES.map((ex) => (
                <button key={ex.id} className="chip" onClick={() => loadExample(ex)}>{ex.label}</button>
              ))}
            </div>
            <button className="btn btn-primary" onClick={run} disabled={running}>
              {running ? <LoaderCircle size={16} className="spin" /> : <Play size={16} />}
              {running ? "Running…" : "Recommend"}
            </button>
          </div>
        </section>

        {result && <ResultView result={result} isSample={isSample} openEvidence={stage === "evidence"} />}
      </div>

      <aside className="stack">
        <section className="card">
          <div className="card-title">Pipeline</div>
          <ol className="steps">
            {PIPELINE_STEPS.map((s, i) => {
              const state = step < 0 || i > step ? "pending" : i < step ? "done" : "active";
              return (
                <li key={s.title} className={`step ${state}`}>
                  <span className="step-icon">
                    {state === "done" ? <Check size={13} strokeWidth={3} /> : state === "active" ? <LoaderCircle size={13} className="spin" /> : i + 1}
                  </span>
                  <div>
                    <div className="step-title">{s.title}</div>
                    <div className="muted small">{state === "active" && stepDetail ? stepDetail : s.detail}</div>
                  </div>
                </li>
              );
            })}
          </ol>
          <div className="hint">Runs take about 30 s to 5 min on Groq's free tier. You can leave this page; the run continues and appears in History.</div>
        </section>
        <section className="card">
          <div className="card-title">Status labels</div>
          <ul className="legend">
            <li><StatusBadge status="verified" /> the cited clause supports the claim</li>
            <li><StatusBadge status="unverified" /> not confirmed by the clause</li>
            <li><StatusBadge status="contradicted" /> the clause says otherwise</li>
          </ul>
        </section>
      </aside>
    </div>
  );
}

function safeParse(m: Manifest): string[] {
  try {
    return parseManifest(m.name, m.content);
  } catch {
    return [];
  }
}
