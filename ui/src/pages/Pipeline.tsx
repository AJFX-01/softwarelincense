import { Brain, Database, FileSearch, Package, ShieldCheck, Sparkles, Workflow } from "lucide-react";

const STEPS = [
  { icon: Package, title: "Input & dependency lookup", text: "Description and/or manifest; PyPI / npm metadata → SPDX IDs." },
  { icon: Sparkles, title: "Stage 1 · recommend", text: "gpt-oss-120b (Groq) infers requirements and picks exactly 3 licenses from the catalogue." },
  { icon: FileSearch, title: "Clause retrieval", text: "Only the clauses relevant to each license's obligations are sent on." },
  { icon: Brain, title: "Stage 2 · explain", text: "3–5 plain-language claims, each citing a clause and quoting it exactly." },
  { icon: ShieldCheck, title: "NLI verifier", text: "DeBERTa-v3-large checks each claim against its clause (runs locally)." },
];

const METRICS = [
  { value: "0.94", label: "NLI entailment precision", note: "“verified” is right 94% of the time" },
  { value: "0.82", label: "NLI accuracy", note: "146 hand-labelled pairs · κ = 0.88" },
  { value: "0.74", label: "Stage 1 Hit@3", note: "correct license in the top 3" },
  { value: "0.56", label: "Stage 1 Hit@1", note: "104 descriptions · 70 profiles" },
];

export function Pipeline() {
  return (
    <div className="stack">
      <section className="metrics">
        {METRICS.map((m) => (
          <div key={m.label} className="card metric">
            <div className="metric-value">{m.value}</div>
            <div className="metric-label">{m.label}</div>
            <div className="muted small">{m.note}</div>
          </div>
        ))}
      </section>

      <section className="card">
        <div className="card-title"><Workflow size={16} /> How v1 works</div>
        <ol className="flow">
          {STEPS.map(({ icon: Icon, title, text }, i) => (
            <li key={title}>
              <span className="flow-icon"><Icon size={18} /></span>
              <div>
                <div className="step-title">{i + 1}. {title}</div>
                <div className="muted small">{text}</div>
              </div>
            </li>
          ))}
        </ol>
      </section>

      <section className="card">
        <div className="card-title"><Database size={16} /> Data</div>
        <ul className="plain-list">
          <li>34 in-scope licenses from choosealicense.com + SPDX (software, OSI-approved)</li>
          <li>Software Heritage license dataset — 20k-file sample for analysis</li>
          <li>729 clause–claim pairs to test the verifier; 190 validated project descriptions to test Stage 1</li>
        </ul>
      </section>
    </div>
  );
}
