import { ChevronRight, FileText, FileUp } from "lucide-react";
import { HISTORY, type Example } from "../mock";

export function History({ onOpen }: { onOpen: (ex: Example) => void }) {
  return (
    <section className="card flush">
      <table className="table">
        <thead>
          <tr><th>When</th><th>Input</th><th>Top pick</th><th>Claims verified</th><th /></tr>
        </thead>
        <tbody>
          {HISTORY.map(({ id, when, example }) => {
            const r = example.result;
            const claims = r.recommendations.flatMap((x) => x.claims);
            const ok = claims.filter((c) => c.status === "verified").length;
            return (
              <tr key={id} className="clickable" onClick={() => onOpen(example)}>
                <td className="muted nowrap">{when}</td>
                <td>
                  <div className="input-cell">
                    {example.manifest ? <FileUp size={15} /> : <FileText size={15} />}
                    <span className="truncate">{example.description}</span>
                  </div>
                  {example.manifest && <div className="muted small mono">{example.manifest.name}</div>}
                </td>
                <td className="mono strong">{r.recommendations[0]?.spdx_id}</td>
                <td className="mono">{ok}/{claims.length}</td>
                <td className="right"><ChevronRight size={16} /></td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </section>
  );
}
