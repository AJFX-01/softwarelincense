"""Phase 2 diagrams: p2_07 system design v2 (what changed), p2_08 CI/CD and branches."""
from diagram_kit import D

NEW, CHG = "ok", "src"  # chip kinds: NEW = green, CHANGED = amber


def tag(d, x, y, label):
    d.chip(x, y, label, NEW if label == "NEW" else CHG)


# ---------------------------------------------------------------- p2_07 system design v2
d = D(1600, 1000, "LicenseWise — Phase 2 System Design",
      "Web UI → FastAPI (async jobs, SQLite) → LLM + NLI pipeline · green = new in Phase 2 · amber = changed")
for i, (kind, label) in enumerate([("llm", "LLM call (Groq, open-weight)"), ("nli", "NLI model (local)"),
                                   ("src", "External service / data"), ("blue", "Storage")]):
    from diagram_kit import K
    fill, stroke = K[kind]
    lx = 40 + i * 230
    d.p.append(f'<rect x="{lx}" y="94" width="16" height="14" rx="3" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>')
    d.text(lx + 24, 106, label, 13, color="#333")

# columns
d.p.append('<rect x="40" y="125" width="290" height="640" rx="12" fill="#F5F9FE" stroke="#2F6DB5" stroke-width="1.8"/>')
d.text(185, 155, "Web UI (React + Vite)", 18, "bold", "#2F6DB5", "middle")
d.p.append('<rect x="370" y="125" width="300" height="640" rx="12" fill="#F2FAF7" stroke="#2E8B6E" stroke-width="1.8"/>')
d.text(520, 155, "Backend API (FastAPI)", 18, "bold", "#2E8B6E", "middle")
d.p.append('<rect x="710" y="125" width="560" height="640" rx="12" fill="#FAFAF9" stroke="#777" stroke-width="1.8"/>')
d.text(990, 155, "licensewise pipeline (Python)", 18, "bold", "#333", "middle")

ui = [("New recommendation", ["description / manifest → POST", "live step progress (polls 1.5 s)"], "CHANGED"),
      ("Result cards + evidence", ["3 licenses · claims with badges", "quoted clause highlighted"], None),
      ("History", ["past runs from the database", "reopen or resume a running job"], "CHANGED"),
      ("License catalogue", ["34 licenses from GET /api/licenses"], "CHANGED"),
      ("Backend status pill", ["connected / offline (30 s check)"], "NEW")]
y = 175
for title, lines, t in ui:
    h = 40 + 20 * len(lines)
    d.box(58, y, 254, h, title, lines, "white", tsize=15, lsize=13)
    if t:
        tag(d, 312 - (18 + 7.6 * len(t)) - 6, y + 8, t)
    y += h + 14
d.text(70, 740, "Phase 1: saved examples only", 13, color="#8A8A85", italic=True)

api = [("POST /api/recommendations", ["→ 202 + job id · same input reuses", "the finished job (saves quota)"], "NEW"),
       ("GET …/recommendations/{id}", ["status · current step · result", "queue position"], "NEW"),
       ("GET /api/recommendations", ["history list"], "NEW"),
       ("GET /api/licenses · /api/health", ["catalogue · model names"], "NEW"),
       ("Job worker (1 thread)", ["runs one pipeline at a time;", "validation: type, size, parse"], "NEW")]
y = 175
for title, lines, t in api:
    h = 40 + 20 * len(lines)
    d.box(388, y, 264, h, title, lines, "white", tsize=14, lsize=13)
    tag(d, 652 - (18 + 7.6 * len(t)) - 6, y + 8, t)
    y += h + 14
d.arrow([(330, 230), (384, 230)], "JSON", 357, 222)
d.arrow([(384, 300), (334, 300)], "poll", 357, 292)

steps = [("1 Input + 2 dependency lookup", ["manifest → PyPI / npm declared licenses → SPDX"], "white", None),
         ("3 Stage 1 · recommend (gpt-oss-120b)", ["prompt v2: catalogue WITH license labels;",
                                                   "check every requirement, then rank"], "llm", "CHANGED"),
         ("4 Clause retrieval", ["only the clauses for the license's labels"], "white", None),
         ("5 Stage 2 · explain (gpt-oss-120b)", ["3–5 claims, each cites a clause + exact quote"], "llm", None),
         ("6 NLI verifier (DeBERTa-v3-large)", ["top 4 layers fine-tuned on 729 license", "clause–claim pairs; quote check first"], "nli", "CHANGED"),
         ("7 Response", ["labelled claims · warnings · timings · progress events"], "white", None)]
y = 175
for title, lines, kind, t in steps:
    h = 40 + 20 * len(lines)
    d.box(728, y, 524, h, title, lines, kind, tsize=15, lsize=13)
    if t:
        tag(d, 1252 - (18 + 7.6 * len(t)) - 6, y + 8, t)
    if y > 175:
        d.arrow([(990, y - 14), (990, y - 2)])
    y += h + 14
d.arrow([(670, 600), (706, 600)], "run()", 688, 592)

# right column: storage & external
d.box(1300, 175, 270, 110, "SQLite database", ["data/runs/licensewise.db", "jobs: id, input_key, status,", "created_at, data JSON"], "blue", tsize=15, lsize=13)
tag(d, 1300 + 270 - 56, 183, "NEW")
d.box(1300, 300, 270, 80, "Groq API", ["gpt-oss-120b · free tier", "200k tokens/day"], "src", tsize=15, lsize=13)
d.box(1300, 395, 270, 80, "PyPI / npm registries", ["declared license per package"], "src", tsize=15, lsize=13)
d.box(1300, 490, 270, 100, "Fine-tuned verifier", ["models/deberta-v3-large-", "license-nli (local, 0.8 GB)"], "nli", tsize=14, lsize=13)
tag(d, 1300 + 270 - 56, 498, "NEW")
d.box(1300, 605, 270, 80, "License knowledge base", ["34 licenses · labels · clauses"], "grey", tsize=15, lsize=13)
d.arrow([(520, 125), (520, 117), (1435, 117), (1435, 171)], dashed=True)
d.text(1180, 111, "job worker saves / loads jobs", 13, color="#444", anchor="middle", italic=True)

# bottom: offline + CI
d.p.append('<rect x="40" y="790" width="1530" height="190" rx="12" fill="none" stroke="#999" stroke-width="1.5" stroke-dasharray="7 5"/>')
d.text(58, 818, "Offline: training, evaluation and CI (not in the request path)", 16, "bold", "#888")
off = [("Threshold tuning", ["tune on 583 auto-labelled pairs", "report on 146 human-labelled"], "nli", "NEW"),
       ("Partial fine-tuning", ["cache frozen layers 0–19", "train layers 20–23 + head · 5-fold CV"], "nli", "NEW"),
       ("Stage 1 evaluation", ["prompt v1 vs v2 · 120b vs 20b", "paired on the same 104 descriptions"], "llm", "CHANGED"),
       ("Tests (pytest, 27)", ["LLM + NLI mocked", "API, parsing, prompts, verifier"], "white", "NEW"),
       ("GitHub Actions CI", ["development + main branches", "ruff · pytest · oxlint · build"], "white", "NEW")]
x = 58
for title, lines, kind, t in off:
    d.box(x, 835, 286, 120, title, lines, kind, tsize=15, lsize=13)
    tag(d, x + 286 - (18 + 7.6 * len(t)) - 6, 843, t)
    x += 300
d.save("p2_07_system_design_v2")

# ---------------------------------------------------------------- p2_08 CI/CD
d = D(1600, 640, "CI/CD and GitHub workflow",
      "Work lands on development; main only changes through a pull request whose checks pass")
d.box(40, 130, 300, 150, "Developer", ["edit code + tests locally", "pytest · ruff · pnpm build", "git push origin development"], "white", lsize=14)
d.box(400, 130, 300, 150, "development branch", ["integration branch", "every push runs CI"], "blue", lsize=14)
d.box(760, 110, 420, 380, "GitHub Actions  (.github/workflows/ci.yml)", [], "white")
d.box(785, 165, 370, 145, "Job: backend  (Python 3.14)", ["pip install -r requirements-ci.txt", "ruff check licensewise scripts tests",
                                                          "pytest -q   (27 tests, LLM + NLI mocked)"], "nli", tsize=15, lsize=13.5)
d.box(785, 325, 370, 145, "Job: ui  (Node 24, pnpm)", ["pnpm install --frozen-lockfile", "pnpm lint     (oxlint)",
                                                      "pnpm build    (tsc type-check + vite)"], "llm", tsize=15, lsize=13.5)
d.box(1240, 130, 320, 150, "Pull request → main", ["development → main", "merge only when backend", "and ui checks are green"], "src", lsize=14)
d.box(1240, 340, 320, 150, "main branch", ["stable, demo-ready", "CI runs again on merge", "(branch protection)"], "blue", lsize=14)
d.arrow([(340, 205), (396, 205)], "push", 368, 197)
d.arrow([(700, 205), (756, 205)], "trigger", 728, 197)
d.arrow([(1180, 205), (1236, 205)], "✓ green", 1208, 197)
d.arrow([(1400, 280), (1400, 336)], "merge", 1420, 314, anchor="start")
d.box(40, 330, 660, 160, "Why the tests need no API key or model", [
    "pipeline.recommend and llm.complete_json are replaced by fakes,",
    "the NLI model call (_nli) returns fixed probabilities, and the",
    "API uses a temporary SQLite file. CI installs no torch/transformers:",
    "fast (< 1 s of tests) and free."], "grey", lsize=14)
d.box(40, 520, 1520, 90, "What the checks protect", [
    "API contract (202 + polling, reuse, 422/404, restart persistence) · manifest parsing · license normalising · Stage 1 prompt variants and retry · verifier quote check and label mapping · UI types and build"],
      "white", lsize=14)
d.save("p2_08_cicd")
