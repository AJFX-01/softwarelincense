// Data samples page: shows the files in examples/samples/ (scripts/build_examples.py).
// The files are fetched from the backend, not bundled, and this page is lazy-loaded
// (see App.tsx), so it adds nothing to the app's first load.

import { useEffect, useState } from "react";
import { Info, LoaderCircle } from "lucide-react";
import { api, ApiError, type SampleInfo } from "../api";

// ?page=samples&sample=06_stage1_phase1_vs_phase2 opens one sample directly
const initial = new URLSearchParams(window.location.search).get("sample");

type Json = string | number | boolean | null | Json[] | { [key: string]: Json };

/** The sample files store long text as a list of short lines; join them back into
 *  paragraphs. A blank line starts a new paragraph; a list item starts a new line. */
function joinLines(lines: string[]): string {
  let text = "";
  for (const line of lines) {
    if (line === "") text += "\n\n";
    else if (!text || text.endsWith("\n")) text += line;
    else if (/^(\d+\.|-|\*)\s/.test(line)) text += "\n" + line;
    else text += " " + line;
  }
  return text;
}

const isObject = (v: Json): v is { [key: string]: Json } => typeof v === "object" && v !== null && !Array.isArray(v);
const isStringList = (v: Json[]): v is string[] => v.every((x) => typeof x === "string");
// Short single words (license IDs, labels): show as tags rather than text
const isTagList = (v: string[]) => v.length > 0 && v.every((x) => x.length <= 40 && !/\s/.test(x));

function label(key: string) {
  return key.replace(/^_about_?/, "about ").replace(/_/g, " ").trim();
}

function Value({ value }: { value: Json }) {
  if (value === null) return <span className="mono muted">null</span>;
  if (typeof value === "boolean" || typeof value === "number") return <span className="mono">{String(value)}</span>;
  if (value === "") return <span className="muted">(empty)</span>;
  if (typeof value === "string") return <span className="sample-text">{value}</span>;
  if (Array.isArray(value)) {
    if (value.length === 0) return <span className="muted">(none)</span>;
    if (isStringList(value)) {
      return isTagList(value)
        ? <span className="sample-tags">{value.map((t, i) => <span key={i} className="tag mono">{t}</span>)}</span>
        : <span className="sample-text">{joinLines(value)}</span>;
    }
    return (
      <div className="sample-list">
        {value.map((item, i) => <div key={i} className="sample-item"><Value value={item} /></div>)}
      </div>
    );
  }
  return <Fields data={value} />;
}

function Fields({ data }: { data: { [key: string]: Json } }) {
  return (
    <dl className="sample-fields">
      {Object.entries(data).map(([key, value]) =>
        key.startsWith("_about") ? (
          <div key={key} className="sample-about">
            <Info size={15} className="icon-muted" />
            <span className="sample-text">{Array.isArray(value) && isStringList(value) ? joinLines(value) : String(value)}</span>
          </div>
        ) : isObject(value) ? (
          // A group of fields: its name as a heading, the fields indented below
          <div key={key} className="sample-group">
            <dt className="mono">{label(key)}</dt>
            <dd><Fields data={value} /></dd>
          </div>
        ) : (
          <div key={key} className="sample-row">
            <dt className="mono">{label(key)}</dt>
            <dd><Value value={value} /></dd>
          </div>
        ))}
    </dl>
  );
}

export function Samples() {
  const [list, setList] = useState<SampleInfo[] | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  // The loaded file, with its name, so a stale file is never shown under a new name
  const [loaded, setLoaded] = useState<{ name: string; data: { [key: string]: Json } } | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.samples().then((items) => { setList(items); setSelected(items.find((i) => i.name === initial)?.name ?? items[0]?.name ?? null); },
      (e) => setError(e instanceof ApiError ? e.message : String(e)));
  }, []);

  useEffect(() => {
    if (!selected) return;
    api.sample(selected).then((d) => setLoaded({ name: selected, data: d as { [key: string]: Json } }),
      (e) => setError(e instanceof ApiError ? e.message : String(e)));
  }, [selected]);

  if (error) return <div className="card empty">{error}</div>;
  if (!list) return <div className="card empty"><LoaderCircle size={16} className="spin" /> Loading samples…</div>;

  const data = loaded?.name === selected ? loaded.data : null;
  const { _title: title, ...fields } = data ?? {};
  return (
    <div className="samples">
      <nav className="card flush sample-nav">
        {list.map((s, i) => (
          <button key={s.name} className={`sample-pick ${s.name === selected ? "active" : ""}`}
                  onClick={() => setSelected(s.name)}>
            <span className="mono muted">{String(i + 1).padStart(2, "0")}</span> {s.title}
          </button>
        ))}
        <div className="hint sample-hint">Copied from the real data files by scripts/build_examples.py</div>
      </nav>
      <section className="card sample-body">
        {data ? (
          <>
            <h2>{typeof title === "string" ? title : selected}</h2>
            <div className="mono muted small">examples/samples/{selected}.json</div>
            <Fields data={fields} />
          </>
        ) : <div className="empty"><LoaderCircle size={16} className="spin" /></div>}
      </section>
    </div>
  );
}
