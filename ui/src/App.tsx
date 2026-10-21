import { useState } from "react";
import type { Page } from "./types";
import { EXAMPLES, type Example } from "./mock";
import { Sidebar, Topbar } from "./components/Shell";
import { NewRecommendation } from "./pages/NewRecommendation";
import { History } from "./pages/History";
import { Licenses } from "./pages/Licenses";
import { Pipeline } from "./pages/Pipeline";

// Demo shortcuts: ?page=licenses · ?example=saas · ?example=clinic
// &stage=input|running|evidence freezes the page at that step (for screenshots)
const params = new URLSearchParams(window.location.search);
const initialPage = (["new", "history", "licenses", "pipeline"].includes(params.get("page") ?? "")
  ? params.get("page") : "new") as Page;
const initialPreset = EXAMPLES.find((e) => e.id === params.get("example")) ?? null;
const stage = params.get("stage") ?? undefined;

export default function App() {
  const [page, setPage] = useState<Page>(initialPage);
  const [preset, setPreset] = useState<Example | null>(initialPreset);

  return (
    <div className="app">
      <Sidebar page={page} onNavigate={(p) => { setPreset(null); setPage(p); }} />
      <div className="main">
        <Topbar page={page} />
        <main className="content">
          {page === "new" && <NewRecommendation key={preset?.id ?? "blank"} preset={preset} stage={preset === initialPreset ? stage : undefined} />}
          {page === "history" && <History onOpen={(ex) => { setPreset(ex); setPage("new"); }} />}
          {page === "licenses" && <Licenses />}
          {page === "pipeline" && <Pipeline />}
        </main>
      </div>
    </div>
  );
}
