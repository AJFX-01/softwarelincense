import type { ReactNode } from "react";
import { CircleCheck, CircleQuestionMark, CircleX, Quote, X } from "lucide-react";
import type { Claim, Status } from "../types";
import { highlight } from "../lib";

const STATUS: Record<Status, { label: string; icon: typeof CircleCheck }> = {
  verified: { label: "Verified", icon: CircleCheck },
  unverified: { label: "Unverified", icon: CircleQuestionMark },
  contradicted: { label: "Contradicted", icon: CircleX },
};

export function StatusBadge({ status }: { status: Status }) {
  const { label, icon: Icon } = STATUS[status];
  return (
    <span className={`badge badge-${status}`}>
      <Icon size={14} strokeWidth={2.2} /> {label}
    </span>
  );
}

export function Drawer({ title, onClose, children }: { title: string; onClose: () => void; children: ReactNode }) {
  return (
    <div className="drawer-backdrop" onClick={onClose}>
      <aside className="drawer" onClick={(e) => e.stopPropagation()}>
        <div className="drawer-head">
          <div className="drawer-title">{title}</div>
          <button className="icon-btn" onClick={onClose} aria-label="Close"><X size={17} /></button>
        </div>
        <div className="drawer-body">{children}</div>
      </aside>
    </div>
  );
}

export function EvidenceDrawer({ claim, license, onClose }: { claim: Claim; license: string; onClose: () => void }) {
  const [before, match, after] = highlight(claim.clause_text ?? "", claim.quote);
  const probs = claim.nli ?? {};
  return (
    <Drawer title={`Evidence · ${license}`} onClose={onClose}>
      <div className="field-label">Claim</div>
      <p className="claim-big">{claim.text}</p>
      <StatusBadge status={claim.status} />
      <p className="muted small">{claim.reason}</p>

      <div className="field-label">Cited clause {claim.clause_id}</div>
      <blockquote className="clause">
        <Quote size={15} className="clause-icon" />
        {claim.clause_text ? (
          <span>{before}<mark>{match}</mark>{after}</span>
        ) : (
          <span className="muted">Clause not available.</span>
        )}
      </blockquote>
      {!claim.quote_found && <p className="warn small">The quoted text was not found in this clause.</p>}

      {claim.nli && (
        <>
          <div className="field-label">NLI verifier (DeBERTa-v3-large)</div>
          {["entailment", "neutral", "contradiction"].map((k) => (
            <div key={k} className="prob-row">
              <span className="prob-name">{k}</span>
              <div className="prob-track"><div className="prob-fill" style={{ width: `${(probs[k] ?? 0) * 100}%` }} /></div>
              <span className="prob-val mono">{((probs[k] ?? 0) * 100).toFixed(0)}%</span>
            </div>
          ))}
          <p className="muted small">Entailment → verified · neutral → unverified · contradiction → contradicted.</p>
        </>
      )}
    </Drawer>
  );
}
