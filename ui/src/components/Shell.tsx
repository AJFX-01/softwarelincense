import type { ReactNode } from "react";
import { Bell, BookOpen, Clock, FileBraces, Plus, Scale, Settings, Terminal, Workflow } from "lucide-react";
import type { Page } from "../types";
import { useBackendOnline } from "../api";

const NAV: { group: string; items: { page: Page; label: string; icon: ReactNode }[] }[] = [
  {
    group: "Workspace",
    items: [
      { page: "new", label: "New recommendation", icon: <Plus size={17} /> },
      { page: "history", label: "History", icon: <Clock size={17} /> },
    ],
  },
  {
    group: "Reference",
    items: [
      { page: "licenses", label: "License catalogue", icon: <BookOpen size={17} /> },
      { page: "pipeline", label: "Pipeline & evaluation", icon: <Workflow size={17} /> },
      { page: "samples", label: "Data samples", icon: <FileBraces size={17} /> },
    ],
  },
];

const PAGE_TITLES: Record<Page, { title: string; subtitle: string }> = {
  new: { title: "New recommendation", subtitle: "Describe your project or upload a manifest" },
  history: { title: "History", subtitle: "Previous recommendations" },
  licenses: { title: "License catalogue", subtitle: "34 OSI-approved software licenses in scope" },
  pipeline: { title: "Pipeline & evaluation", subtitle: "How v1 works and how well it does" },
  samples: { title: "Data samples", subtitle: "What each kind of data looks like, from the real files" },
};

export function Sidebar({ page, onNavigate }: { page: Page; onNavigate: (p: Page) => void }) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark"><Scale size={18} /></div>
        <div>
          <div className="brand-name">LicenseWise</div>
          <div className="brand-sub">v1 · LLM + NLI</div>
        </div>
      </div>

      <nav>
        {NAV.map((g) => (
          <div key={g.group} className="nav-group">
            <div className="nav-label">{g.group}</div>
            {g.items.map((item) => (
              <button
                key={item.page}
                className={`nav-item ${page === item.page ? "active" : ""}`}
                onClick={() => onNavigate(item.page)}
              >
                {item.icon}
                <span>{item.label}</span>
              </button>
            ))}
          </div>
        ))}
      </nav>

      <div className="sidebar-foot">
        <div className="cli-card">
          <div className="cli-title"><Terminal size={15} /> Prefer the terminal?</div>
          <code>python scripts/recommend.py --manifest requirements.txt</code>
        </div>
        <div className="legal">Explanations are based on license text only. Not legal advice.</div>
      </div>
    </aside>
  );
}

export function Topbar({ page }: { page: Page }) {
  const { title, subtitle } = PAGE_TITLES[page];
  const online = useBackendOnline();
  return (
    <header className="topbar">
      <div>
        <div className="crumbs">LicenseWise <span>/</span> {title}</div>
        <div className="subtitle">{subtitle}</div>
      </div>
      <div className="topbar-right">
        <span className="pill" title={online === false ? "Start it with: .venv/bin/uvicorn licensewise.api:app --port 8000" : undefined}>
          <span className={online ? "dot dot-ok" : online === false ? "dot dot-bad" : "dot"} />
          {online ? "Backend connected" : online === false ? "Backend offline" : "Checking backend…"}
        </span>
        <span className="pill mono">gpt-oss-120b · DeBERTa-v3</span>
        <button className="icon-btn" aria-label="Notifications"><Bell size={17} /></button>
        <button className="icon-btn" aria-label="Settings"><Settings size={17} /></button>
        <div className="avatar">LW</div>
      </div>
    </header>
  );
}
