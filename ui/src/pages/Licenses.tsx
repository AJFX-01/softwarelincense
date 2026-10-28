import { useEffect, useMemo, useState } from "react";
import { Check, Minus, Search } from "lucide-react";
import { LICENSES } from "../mock";
import { api } from "../api";
import { COPYLEFT_LABEL, humanize } from "../lib";
import type { License } from "../types";
import { Drawer } from "../components/Evidence";

const FILTERS: { key: "all" | License["copyleft"]; label: string }[] = [
  { key: "all", label: "All" },
  { key: "none", label: "Permissive" },
  { key: "file_or_library", label: "Weak copyleft" },
  { key: "whole_work", label: "Strong copyleft" },
];

const COLUMNS: { label: string; has: (l: License) => boolean }[] = [
  { label: "Patent grant", has: (l) => l.permissions.includes("patent-use") },
  { label: "Disclose source", has: (l) => l.conditions.includes("disclose-source") },
  { label: "Same license", has: (l) => l.conditions.some((c) => c.startsWith("same-license")) },
  { label: "Network clause", has: (l) => l.conditions.includes("network-use-disclose") },
  { label: "No trademark rights", has: (l) => l.limitations.includes("trademark-use") },
];

function Mark({ on }: { on: boolean }) {
  return on ? <Check size={16} strokeWidth={2.5} /> : <Minus size={14} className="icon-faint" />;
}

export function Licenses() {
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<(typeof FILTERS)[number]["key"]>("all");
  const [open, setOpen] = useState<License | null>(null);
  const [licenses, setLicenses] = useState<License[]>(LICENSES); // saved copy until the backend answers

  useEffect(() => {
    api.licenses().then(setLicenses, () => {});
  }, []);

  const rows = useMemo(() => {
    const q = query.toLowerCase();
    return licenses.filter((l) => (filter === "all" || l.copyleft === filter) &&
      (l.spdx_id.toLowerCase().includes(q) || l.title.toLowerCase().includes(q)));
  }, [licenses, query, filter]);

  return (
    <div className="stack">
      <div className="toolbar">
        <label className="search">
          <Search size={16} />
          <input placeholder="Search licenses" value={query} onChange={(e) => setQuery(e.target.value)} />
        </label>
        <div className="segmented">
          {FILTERS.map((f) => (
            <button key={f.key} className={filter === f.key ? "active" : ""} onClick={() => setFilter(f.key)}>{f.label}</button>
          ))}
        </div>
      </div>

      <section className="card flush">
        <table className="table">
          <thead>
            <tr>
              <th>License</th><th>Type</th>
              {COLUMNS.map((c) => <th key={c.label} className="center">{c.label}</th>)}
            </tr>
          </thead>
          <tbody>
            {rows.map((l) => (
              <tr key={l.spdx_id} className="clickable" onClick={() => setOpen(l)}>
                <td>
                  <div className="mono strong">{l.spdx_id}</div>
                  <div className="muted small">{l.title}</div>
                </td>
                <td><span className="tag">{COPYLEFT_LABEL[l.copyleft]}</span></td>
                {COLUMNS.map((c) => <td key={c.label} className="center"><Mark on={c.has(l)} /></td>)}
              </tr>
            ))}
          </tbody>
        </table>
        {rows.length === 0 && <div className="empty">No licenses match.</div>}
      </section>

      {open && (
        <Drawer title={open.spdx_id} onClose={() => setOpen(null)}>
          <p className="claim-big">{open.title}</p>
          <span className="tag">{COPYLEFT_LABEL[open.copyleft]}</span>
          {open.language !== "en" && <p className="warn small">License text is not in English; claims about it cannot be NLI-verified.</p>}
          <p className="muted">{open.description}</p>
          {(["permissions", "conditions", "limitations"] as const).map((k) => (
            <div key={k}>
              <div className="field-label">{k}</div>
              <ul className="plain-list">
                {open[k].length ? open[k].map((x) => <li key={x}>{humanize(x)}</li>) : <li className="muted">none</li>}
              </ul>
            </div>
          ))}
          <p className="muted small">Source: choosealicense.com labels.</p>
        </Drawer>
      )}
    </div>
  );
}
