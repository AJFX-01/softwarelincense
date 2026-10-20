import { useState } from "react";
import { ChevronRight, CircleAlert, CircleCheck, CircleQuestionMark, Download, Info, Package, TriangleAlert } from "lucide-react";
import type { Claim, Result } from "../types";
import { EvidenceDrawer, StatusBadge } from "./Evidence";

function download(result: Result) {
  const blob = new Blob([JSON.stringify(result, null, 2)], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "licensewise-result.json";
  a.click();
  URL.revokeObjectURL(a.href);
}

export function ResultView({ result, isSample }: { result: Result; isSample: boolean }) {
  const [evidence, setEvidence] = useState<{ claim: Claim; license: string } | null>(null);
  const claims = result.recommendations.flatMap((r) => r.claims);
  const verified = claims.filter((c) => c.status === "verified").length;
  const conflictDeps = new Set(result.conflicts.map((c) => c.dependency));

  return (
    <div className="stack">
      {isSample && (
        <div className="notice">
          <Info size={16} /> Demo mode: the backend is not connected, so this is a saved result from the real pipeline.
        </div>
      )}

      <div className="results-head">
        <div>
          <h2>Results</h2>
          <div className="muted small">
            {result.recommendations.length} licenses · {verified}/{claims.length} claims verified · {result.timings.total_s}s ·{" "}
            <span className="mono">{result.model}</span>
          </div>
        </div>
        <button className="btn" onClick={() => download(result)}><Download size={16} /> Download JSON</button>
      </div>

      <section className="card">
        <div className="card-title">What we understood</div>
        <ul className="req-list">
          {result.requirements.map((r, i) => (
            <li key={i}>
              <CircleCheck size={16} className="icon-muted" />
              <span>{r.text}</span>
              <span className="tag">{r.source}</span>
            </li>
          ))}
        </ul>
        {result.conflicts.map((c, i) => (
          <div key={i} className="callout callout-warn">
            <TriangleAlert size={16} />
            <span><b>{c.dependency}</b> ({c.dependency_license}): {c.issue}</span>
          </div>
        ))}
        {result.clarifying_questions.map((q, i) => (
          <div key={i} className="callout">
            <CircleQuestionMark size={16} />
            <span>{q}</span>
          </div>
        ))}
      </section>

      {result.dependencies.length > 0 && (
        <section className="card">
          <div className="card-title"><Package size={16} /> Dependencies ({result.dependencies.length})</div>
          <table className="table fixed">
            <colgroup>
              <col style={{ width: "24%" }} /><col style={{ width: "11%" }} /><col style={{ width: "22%" }} />
              <col style={{ width: "25%" }} /><col style={{ width: "18%" }} />
            </colgroup>
            <thead>
              <tr><th>Package</th><th>Ecosystem</th><th>Declared</th><th>SPDX</th><th>Status</th></tr>
            </thead>
            <tbody>
              {result.dependencies.map((d) => (
                <tr key={d.name}>
                  <td className="mono cut" title={d.name}>{d.name}</td>
                  <td>{d.ecosystem}</td>
                  <td className="muted cut" title={d.declared}>{d.declared}</td>
                  <td className="mono cut" title={d.license ?? ""}>{d.license ?? "—"}</td>
                  <td>
                    {!d.license ? (
                      <span className="badge badge-unverified"><CircleQuestionMark size={14} /> Unknown</span>
                    ) : conflictDeps.has(d.name) ? (
                      <span className="badge badge-contradicted"><CircleAlert size={14} /> Constraint</span>
                    ) : (
                      <span className="badge badge-verified"><CircleCheck size={14} /> OK</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {result.recommendations.map((rec) => {
        const ok = rec.claims.filter((c) => c.status === "verified").length;
        return (
          <section key={rec.spdx_id} className="card rec">
            <div className="rec-head">
              <div className="rank">{rec.rank}</div>
              <div className="rec-titles">
                <div className="rec-id">{rec.spdx_id}</div>
                <div className="muted">{rec.title}</div>
              </div>
              <div className="rec-score">
                <span className="mono">{ok}/{rec.claims.length}</span>
                <span className="muted small">claims verified</span>
              </div>
            </div>
            <p className="rec-reason">{rec.reason}</p>
            {rec.note && <div className="callout"><Info size={16} /> {rec.note}</div>}
            <ul className="claims">
              {rec.claims.map((c, i) => (
                <li key={i} className="claim" onClick={() => setEvidence({ claim: c, license: rec.spdx_id })}>
                  <StatusBadge status={c.status} />
                  <div className="claim-text">
                    <div>{c.text}</div>
                    <div className="claim-quote">{c.clause_id} · “{c.quote.length > 110 ? c.quote.slice(0, 110) + "…" : c.quote}”</div>
                  </div>
                  <button className="link">Evidence <ChevronRight size={15} /></button>
                </li>
              ))}
            </ul>
          </section>
        );
      })}

      <div className="disclaimer"><Info size={15} /> {result.disclaimer}</div>

      {evidence && <EvidenceDrawer claim={evidence.claim} license={evidence.license} onClose={() => setEvidence(null)} />}
    </div>
  );
}
