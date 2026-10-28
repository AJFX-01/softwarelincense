import { useEffect, useState } from "react";
import { ChevronRight, CircleAlert, FileText, FileUp, LoaderCircle } from "lucide-react";
import type { Example } from "../mock";
import { api, type JobSummary } from "../api";

export function History({ onOpen }: { onOpen: (ex: Example) => void }) {
  const [runs, setRuns] = useState<JobSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.history().then(setRuns, (e) => setError((e as Error).message));
  }, []);

  async function open(run: JobSummary) {
    try {
      const job = await api.job(run.id);
      onOpen({
        id: job.id,
        label: "",
        description: job.input.description ?? "",
        manifest: job.input.manifest,
        result: job.result, // null for a queued, running or failed run: the page polls it
        jobId: job.id,
      });
    } catch (e) {
      setError((e as Error).message);
    }
  }

  if (error) return <div className="callout callout-error"><CircleAlert size={16} /> {error}</div>;
  if (!runs) return <div className="empty"><LoaderCircle size={16} className="spin" /></div>;

  return (
    <section className="card flush">
      {runs.length === 0 ? (
        <div className="empty">No runs yet. Start one from New recommendation.</div>
      ) : (
        <table className="table">
          <thead>
            <tr><th>When</th><th>Input</th><th>Top pick</th><th>Claims verified</th><th /></tr>
          </thead>
          <tbody>
            {runs.map((run) => (
              <tr key={run.id} className="clickable" onClick={() => open(run)}>
                <td className="muted nowrap">{formatWhen(run.created_at)}</td>
                <td>
                  <div className="input-cell">
                    {run.manifest_name ? <FileUp size={15} /> : <FileText size={15} />}
                    <span className="truncate">{run.description ?? "(manifest only)"}</span>
                  </div>
                  {run.manifest_name && <div className="muted small mono">{run.manifest_name}</div>}
                </td>
                {run.status === "done" ? (
                  <>
                    <td className="mono strong">{run.top_pick}</td>
                    <td className="mono">{run.claims_verified}/{run.claims_total}</td>
                  </>
                ) : (
                  <td colSpan={2} className={run.status === "failed" ? "warn small" : "muted small"}>
                    {run.status === "failed" ? "Failed" : run.status === "queued" ? "Queued" : "Running…"}
                  </td>
                )}
                <td className="right"><ChevronRight size={16} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}

function formatWhen(iso: string): string {
  return new Date(iso).toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
}
