# Phase 2 — Slide Content

Placeholders: **[TEAM]** = only your team can fill · **[FINAL]** = number updates when the Stage 1 runs finish (re-run `notebooks/phase2_results.ipynb`).
Figures: `docs/figures/p2_*.png` (from `notebooks/phase2_results.ipynb` and `docs/tools/make_phase2.py`). Order follows the Phase 2 rubric: Phase 1 overview → software solution → ML components → results → future work → conclusion → demo.

---

## 1. Title
**LicenseWise: Software Licensing Explainability with LLMs**
- ENSF 621 · Phase 2 · Opeyemi Ajegbomogun · Okemawo Obadofin
- Recommend an open-source license → explain it → verify every claim against the license text

---

## 2. Phase 1 in One Slide
- **Built:** a two-stage pipeline (LLM recommends 3 licenses → LLM explains them with claims that quote a clause → an NLI model checks every claim) plus a CLI and a demo React UI
- **Data, all without a legal expert:** 34-license knowledge base (choosealicense + SPDX) · 77 requirement profiles → 190 validated project descriptions (RQ1) · 729 clause–claim pairs, 146 hand-labelled, κ = 0.88 (RQ2)
- **Phase 1 results**

| | Result |
|---|---|
| RQ1 Stage 1 (104 descriptions) | Hit@1 0.56 · Hit@3 0.74 · only 0.60 Hit@3 when 1–3 licenses fit |
| RQ2 Verifier (146 pairs) | DeBERTa accuracy 0.815 · "Verified" precision 0.944 · but confirms only 69% of true claims |
| RQ3 (2 demo runs) | 100% quotes found verbatim · 58% of claims verified |

- **Phase 1 left open:** UI not connected to a backend · verifier misses true claims · recommender breaks stated requirements (trademark 54%, change notes 39%)

---

## 3. Problem and Solution
**Problem (the pain)**
- Developers pick licenses with little legal training, and misunderstand copyleft and patent terms
- Two failures: **wrong fit** (the license doesn't protect what they care about) and **clashes** with dependency licenses
- Existing help: decision quizzes are generic, scanners audit *after* the fact, lawyers are slow and costly
- LLM chatbots explain well but are **confidently wrong**, and in licensing a confident wrong answer is worse than none

**Solution (our innovation)**
- An LLM recommends and explains **only from a curated catalogue**, and every claim must **quote a clause**
- An **independent NLI verifier**, fine-tuned on license language, marks each claim *verified / unverified / contradicted*, with the clause one click away
- An **expert-free evaluation**: ground truth computed from public license labels, not opinion

**Why it matters:** licensing is one of the first decisions in every open-source project; a checkable, project-specific answer lowers legal risk for students and small teams

---

## 4. Related Work and the Gap
| Area | Representative work | What it does | What's missing for our users |
|---|---|---|---|
| Developer studies | Almeida et al. 2017; Wu et al. 2024 | Developers misunderstand terms and combinations | Shows the need; no tool |
| License identification | Ninka; ScanCode; LtRecognizer | Find which license / term is in a file | Identify, don't **recommend** |
| Compatibility & compliance | Kapitsaki et al. (SPDX); LiDetector; OSADL matrix | Detect incompatibilities in existing code | Audit **after** code is written; no explanation |
| Decision guides | choosealicense.com | A few generic paths | Not project-specific; ignores dependencies; no "why" |
| Faithfulness / NLI | SummaC; TRUE; MNLI, ANLI | Detect unsupported generated text | Not applied to legal license text |
| Grounded generation | RAG (Lewis et al. 2020) | Ground output in retrieved passages | Grounding ≠ checking; no per-claim verdict |

**Gap:** no tool both **recommends** a license for a specific project *before* coding and **verifies** its own plain-language explanation against the license text. LicenseWise combines recommendation, clause-quoting explanation, and per-claim NLI verification.

---

## 5. Research Questions (refined for Phase 2)
- **RQ1 — Requirement-to-license mapping.** To what extent can an open-weight LLM, conditioned on a curated license catalogue, map natural-language project requirements to licenses that satisfy them; how does accuracy vary with requirement specificity; **and how much does grounding the model in the catalogue's license labels improve it?**
- **RQ2 — Claim verification.** How reliably can NLI models, **off the shelf and adapted to license text by fine-tuning**, verify LLM-generated claims against the clauses they cite, as measured on human-validated clause–claim pairs?
- **RQ3 — Explanation faithfulness.** To what extent are LLM-generated license explanations grounded in the cited license text (quote fidelity, entailment), and how does NLI verification change the claims shown to developers compared with an unverified baseline?

**Bold** = Phase 2 additions; the Phase 1 questions are unchanged otherwise.

---

## 5b. The RQs in Shaw's (2003) Terms
| | Question type | Result type | Validation |
|---|---|---|---|
| **RQ1** | Method of development: can an LLM + catalogue do requirement → license? | Procedure/technique (prompt v1 → v2) | Analysis: controlled, paired experiment on 104 descriptions with computed answer keys |
| **RQ2** | Method for analysis: can NLI check claims about license text? | Technique + empirical model (fine-tuned verifier) | Analysis: grouped cross-validation on 729 pairs, human-labelled test set |
| **RQ3** | Characterisation of a particular system | Specific solution (the verified pipeline) | Evaluation: verified vs unverified claims on real runs |

---

## 6. What Changed in Phase 2 — at a Glance
| Area | Phase 1 | Phase 2 | Why |
|---|---|---|---|
| UI ↔ backend | UI showed saved examples | **FastAPI backend**, live runs, history | Real tool, real demo |
| Storage | none | **SQLite** job history | Survives restarts; queryable |
| Engineering | manual checks | **27 tests · ruff · GitHub Actions** on `development` + `main` | CI/CD; catch regressions |
| Verifier | off-the-shelf DeBERTa, argmax | **threshold tuned**, then **top 4 layers fine-tuned** on our pairs | Base model missed 31% of true claims |
| Stage 1 prompt | catalogue = title + description | **v2: + license labels; "check every requirement, then rank"** | Most wrong picks broke a stated constraint |
| Stage 1 model | gpt-oss-120b only | **compared with gpt-oss-20b** | Cost/latency trade-off |

---

## 7. Architecture Evolution
*(insert `docs/figures/p2_07_system_design_v2.png`)*
- The Phase 1 design already planned **Web UI → FastAPI → pipeline**; Phase 2 built it
- **Changed:** REST shape (`/api/recommendations` + polling instead of `/recommend` + `/jobs/{id}`), job store in **SQLite** instead of an in-memory cache, Stage 1 prompt v2, fine-tuned verifier
- **Not built (kept as future work):** rules engine and OSADL compatibility check (Phase 1 "v2" plan); RAG still replaced by deterministic clause retrieval
- Why the async job design: one run takes 30 s – 5 min on the free tier → `POST` returns **202 + job id** at once; the UI polls every 1.5 s and shows the current step

---

## 8. Implementation Details
| Layer | Technology | Notes |
|---|---|---|
| Code repo | GitHub `AJFX-01/softwarelincense` | branches `development` → `main` |
| Front end | React 19 + TypeScript + Vite, lucide icons | pages: New recommendation · History · Licenses; Vite proxies `/api` |
| Backend | FastAPI + Uvicorn (Python 3.14) | 5 endpoints, 1 worker thread, input validation (type, size, parse) |
| Database | SQLite (stdlib `sqlite3`) | `jobs(id, input_key, status, created_at, data JSON)` |
| LLM | gpt-oss-120b via Groq (open-weight) | strict JSON-schema output; Stage 1 + Stage 2 |
| Verifier | DeBERTa-v3-large NLI, top 4 of 24 layers fine-tuned (PyTorch, Transformers, Apple MPS) | runs locally, 0.8 GB |
| Data | choosealicense, SPDX, Software Heritage, PyPI/npm | built by `scripts/` |
| Quality | pytest, ruff, oxlint, tsc | `tests/`, `pyproject.toml` |
| Reproducibility | pinned `requirements*.txt`, seeds, `PROJECT_LOG.txt` (every decision + reason) | |

---

## 9. Database
- **Why SQLite:** single-user demo → no server to run; atomic writes (a crash can't leave half a record); history queryable by status and time; in the Python standard library
- **Schema:** `jobs(id TEXT PK, input_key TEXT, status TEXT, created_at TEXT, data TEXT/JSON)` + index on `created_at`
  - `input_key` = SHA-256 of (model, description, manifest, verify) → an identical request **reuses** the finished result instead of spending LLM quota again
  - `data` keeps the full nested pipeline result as JSON (its shape is still evolving)
- **Restart safety:** on startup, jobs left *queued/running* are marked failed with a clear message; Phase 1 JSON job files are imported once
- Manifests are stored only as part of the user's own run history on the local machine

---

## 10. CI/CD and GitHub Integration with the UI
*(insert `docs/figures/p2_08_cicd.png`)*
- **Branches:** `development` = integration · `main` = stable, demo-ready; `main` changes only by a pull request with green checks
- **GitHub Actions** (`.github/workflows/ci.yml`) on every push/PR to either branch:
  - **backend:** `ruff check` + `pytest` (27 tests)
  - **ui:** `pnpm install --frozen-lockfile` → `oxlint` → `tsc` type-check + `vite build`
- **Tests need no API key or model:** the LLM and NLI calls are mocked → CI is fast and free
- The tests found a real bug: the API's worker pool was created at import, so the app could not restart in one process → fixed
- **[TEAM]** screenshot of the green Actions run + the merged PR

---

## 11. How the UI Talks to the Backend
| UI action | API call | What the user sees |
|---|---|---|
| Open the app | `GET /api/health` (every 30 s) | "Backend connected / offline" pill |
| Press **Recommend** | `POST /api/recommendations` → 202 + id | run starts (or reuses an identical past run) |
| While running | `GET /api/recommendations/{id}` every 1.5 s | live step: dependencies → Stage 1 → retrieval → explain → verify, queue position |
| Open **History** | `GET /api/recommendations` | past runs: top pick, claims verified, status |
| Open **Licenses** | `GET /api/licenses` | 34 licenses with labels and copyleft level |
- Friendly errors: Groq rate limit, missing API key, invalid or empty manifest (422 before any LLM call)

---

## 12. ML — What Changed Since Phase 1
- **Data:** no new labelling. The same 729 clause–claim pairs became **training data** via 5-fold cross-validation; target = human label where one exists (146), otherwise the automatic label (97.9% agree with humans)
- **Leakage control:** folds **grouped by license** (main) and, as a stress test, **grouped by claim template** (all wordings of e.g. "commercial use allowed" held out together)
- **Transformation:** the frozen lower layers' outputs are computed once and **cached** (float16) → training touches only the top layers; fits a 16 GB laptop
- **Stage 1 data:** the same 104 descriptions as Phase 1 → every comparison is **paired**
- **Evaluation:** unchanged metrics, so Phase 1 and Phase 2 numbers compare directly

---

## 13. ML — Configurations Explored (Verifier, RQ2)
*(insert `docs/figures/p2_02_verifier_configs.png`)*

| Configuration (146 human-labelled pairs) | Accuracy | "Verified" precision | True claims confirmed |
|---|---|---|---|
| Base DeBERTa, argmax (Phase 1) | 0.815 | 0.944 | 0.694 |
| Base, threshold t = 0.10 (ML-5) | 0.829 | 0.925 | 0.755 |
| Fine-tuned, top 2 layers | 0.897 | 0.936 | 0.898 |
| **Fine-tuned, top 4 layers** | **0.925** | **0.978** | **0.918** |
| Fine-tuned top 4, unseen claim wording | 0.911 | 0.933 | 0.857 |
- Also tried: top 8 layers → did not fit in memory (stopped); RoBERTa-large stayed behind (Phase 1)
- **Threshold:** chosen on the 583 *unlabelled-by-humans* pairs (best macro-F1 with precision ≥ 0.90), then reported on the human set → *(insert `p2_01_threshold_curve.png`)*

---

## 14. ML — Fine-Tuning Setup and Hyperparameters
| Choice | Value | Why |
|---|---|---|
| Base model | DeBERTa-v3-large NLI (MNLI/FEVER/ANLI/LING/WANLI) | Best Phase 1 verifier |
| Trainable | top **K = 4** of 24 layers + pooler + classifier | K=2 under-fits; K=8 out of memory; 729 pairs too few for full fine-tuning |
| Optimiser | AdamW, lr 2e-5, weight decay 0.01, 10% warm-up, grad-clip 1.0 | Standard for DeBERTa fine-tuning |
| Epochs / batch | 3 / 8 (length-grouped batches) | Small data; avoids padding waste |
| Validation | 5-fold grouped CV, out-of-fold predictions | Every pair scored by a model that never saw it |
| Final model | retrained on all 729 pairs (~4 min) | Deployed in the app |
- **Engineering fixes that made it run:** cache frozen layers (stopped 13 GB swapping) · float32 only for trained layers · clear MPS cache every 20 steps (epoch 33 min → 63 s) · `caffeinate` for overnight runs

---

## 15. ML — Results vs Baseline (Verifier)
*(insert `docs/figures/p2_03_confusion_base_vs_finetuned.png`)*
- Accuracy **0.815 → 0.925**; true claims confirmed **69% → 92%**; "verified" precision **0.944 → 0.978**
- Errors fall from 27 to 11 of 146; only 1 neutral claim marked verified, no contradiction marked verified
- **Against the requirement** (NFR Faithfulness: "verified" precision ≥ 0.90): met in both settings (0.978 and 0.933)
- **On real Stage 2 claims** (37 claims from saved runs; not human-labelled): verified **24 → 32**, unverified 11 → 4, contradicted 2 → 1; all 8 changes read as correct

---

## 16. ML — Is It Memorising? (Generalisation Check)
*(insert `docs/figures/p2_04_template_memorisation.png`)*
- Held out **whole claim templates** to test wording never seen in training
- **Generalises:** patent-use 0.41 → 0.94 · trademark 0.55 → 1.00 · warranty 0.75 → 0.97, even when unseen
- **Partly memorised:** commercial-use 0.21 → 1.00 when seen, but only **0.33** unseen; disclose-source 0.46 → 0.77 seen, 0.54 unseen
- New cost: with unseen wording, **1 contradiction was marked verified** (base model: 0)
- → report both scores; the unseen-wording score (0.911) is the honest estimate for new claims

---

## 17. ML — Stage 1 Configurations (RQ1)  **[FINAL]**
*(insert `docs/figures/p2_05_stage1_configs.png`)*

| Configuration (paired descriptions, n = 68 interim **[FINAL: 104]**) | Hit@1 | Hit@3 | Precision@3 |
|---|---|---|---|
| v1 prompt · gpt-oss-120b (Phase 1) | 0.588 | 0.765 | 0.588 |
| **v2 prompt (labels + check-then-rank) · gpt-oss-120b** | **0.882** | **0.941** | **0.868** |
| v1 prompt · gpt-oss-20b | 0.559 | 0.735 | 0.578 |
- **One** new prompt, designed from the Phase 1 error analysis before any new results → no tuning on the test set
- Smaller model: ~12% fewer tokens but slightly worse → keep gpt-oss-120b
- Cost of v2: ~6k tokens per description vs ~4.2k; 3 requests too large for the free tier's per-minute limit

---

## 18. ML — Where Stage 1 Still Fails
*(insert `docs/figures/p2_06_stage1_violations.png`)*

| Requirement broken (share of picks) | v1 | v2 |
|---|---|---|
| Trademark not granted | 0.51 | **0.04** |
| No need to document changes | 0.33 | **0.10** |
| Network use triggers source sharing | 0.13 | **0.01** |
| Copyleft level (share changes) | 0.28 | 0.26 |
- Labels fixed the requirements they spell out directly
- **Copyleft level barely moved:** every remaining case asks for **weak copyleft** (LGPL/MPL-style) plus another requirement, with only 2–4 fitting licenses; the model falls back to permissive licenses (Apache-2.0, MulanPSL-2.0)
- Not patched now: changing the prompt after seeing test results would tune on the test set → future work

---

## 19. Evaluation Against the Requirements
| Requirement | Target | Phase 2 status |
|---|---|---|
| FR1/FR2 Input (description / manifest) | both, either alone | ✅ in UI and API, validated |
| FR4 Recommend 3 fitting licenses | — | ✅ Hit@3 0.94 **[FINAL]** (Phase 1: 0.74) |
| FR5 Explain with cited clauses | every claim quotes a clause | ✅ |
| FR6 Verify each claim | verified / unverified / contradicted | ✅ fine-tuned verifier |
| NFR Faithfulness | "verified" precision ≥ 0.90 | ✅ 0.978 (0.933 on unseen wording) |
| NFR Latency | < 5 min on free tier | ✅ ~30–35 s in our test runs; longer when queued or rate-limited |
| NFR Cost | free tier + local model | ✅ |
| NFR Reproducibility / maintainability | versioned, modular, tested | ✅ pinned deps, tests, CI, log |
| NFR Security & robustness | file type/size limits, never execute input | ✅ checked before any LLM call |

---

## 20. Strengths and Weaknesses
**Strengths**
- Correct license in the top 3 for ~94% of descriptions **[FINAL]**; top pick right ~88% (Phase 1: 56%)
- "Verified" is reliable: precision 0.98, and it now confirms 92% of true claims (Phase 1: 69%)
- Every claim is traceable to an exact clause; full system runs on free tiers and a laptop
- Tested, CI-checked, reproducible; every decision logged with its reason

**Weaknesses**
- Weak-copyleft requests still often get permissive picks
- Part of the verifier gain is memorised claim wording; 1 false "verified" on unseen wording
- Test descriptions are LLM-written from profiles, not by real developers
- Real Stage 2 claims only previewed, not human-labelled; RQ3 baseline comparison is small
- v2 prompt costs ~40% more tokens; free-tier quota limits evaluation size

---

## 21. Key Findings and Impact
1. **Grounding beats model size:** giving the LLM the license labels lifted Hit@1 from 0.59 to 0.88 **[FINAL]**; a smaller model with the old prompt did worse
2. **Domain adaptation fixes the verifier's blind spot:** fine-tuning 4 layers on 729 pairs confirms 92% of true claims instead of 69% while keeping precision above 0.9
3. **Cheap enough for a laptop:** caching frozen layers turned an out-of-memory job into a 4-minute training run
4. **Expert-free evaluation works:** computed answer keys + a small human-checked set gave clear, paired comparisons
- **Impact:** a developer gets a project-specific license choice with explanations they can check clause by clause, instead of a generic quiz or an unverifiable chatbot answer

---

## 22. Future Work
- Explain copyleft labels in the prompt and re-test on **new** descriptions (fixes the weak-copyleft gap)
- Paraphrase claim templates for fine-tuning → less memorisation; human-label real Stage 2 claims (full RQ3)
- Rules engine + OSADL compatibility matrix for dependency conflicts (deterministic checks after the LLM)
- Compact catalogue (labels only) to stay under per-request limits; self-consistency voting for Stage 1
- User study with developers on clarity and trust; more licenses (non-OSI, custom); deploy behind auth

---

## 23. Conclusion
- **Phase 2 delivered:** a connected web app (FastAPI + SQLite + React), CI/CD on two branches, a fine-tuned verifier, and a label-grounded recommender
- **Against the baseline:** recommendation Hit@1 0.56 → ~0.88 **[FINAL]**; verifier accuracy 0.815 → 0.925 with "verified" precision 0.98
- **Overall project:** LicenseWise shows that an LLM plus an independent, domain-adapted verifier can give **project-specific, checkable** license advice, and that it can be evaluated rigorously without a legal expert
- Not legal advice, but a faster, transparent first step

---

## 24. Demo
1. **Backend connected** pill → **New recommendation**: "SaaS analytics library; companies running it as a service must share improvements" → watch the live steps → AGPL-3.0 first
2. Open a claim → **evidence**: the quoted clause highlighted, NLI scores
3. **Upload manifest** (`requirements.txt` with `pyqt5`) → GPL-3.0 dependency flagged → recommendations respect it
4. Submit the same input again → **reused instantly** (no new LLM call)
5. **History** (from SQLite) → reopen a past run
6. GitHub: green **Actions** run on `development` → PR → `main`
- Backup: saved runs in History if Groq is rate-limited during the demo

---

## 25. Individual Contributions **[TEAM]**
- Opeyemi Ajegbomogun — …
- Okemawo Obadofin — …

---

# Figures (Phase 2)
| Figure | Supports | Takeaway |
|---|---|---|
| `p2_01_threshold_curve.png` | 13 | Lower threshold → more true claims confirmed, until precision drops below 0.90 |
| `p2_02_verifier_configs.png` | 13 | Fine-tuning the top 4 layers lifts every verifier metric |
| `p2_03_confusion_base_vs_finetuned.png` | 15 | Errors 27 → 11; misses of true claims mostly gone |
| `p2_04_template_memorisation.png` | 16 | Most gains survive unseen wording; commercial-use is memorised |
| `p2_05_stage1_configs.png` | 17 | Prompt v2 beats v1 and the smaller model |
| `p2_06_stage1_violations.png` | 18 | Labels fix trademark/change-notes violations; copyleft level doesn't move |
| `p2_07_system_design_v2.png` | 7 | What's new and changed in the architecture |
| `p2_08_cicd.png` | 10 | Branches, CI jobs, merge gate |
