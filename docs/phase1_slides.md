# Phase 1 — Slide Content

Placeholders: **[TEAM]** = only your team can fill.
Charts are grouped in the **Figures** section at the end (A1–A4), referenced as → Fig. A#. Files: `docs/figures/` (from `notebooks/phase1_results.ipynb`); diagram: `docs/system_design.png`.

---

## 1. Title
**LicenseWise: Software Licensing Explainability with LLMs**
- ENSF 621 · Phase 1 · [TEAM: names]
- Recommend an open-source license → explain it → verify every claim

---

## 2. Problem
- Every piece of shared software comes with a **license**: the legal rules for how others may use, change and sell it
- Developers often pick one **without reading it**, and it goes wrong in two ways:
  - **Wrong fit:** the license doesn't protect what they actually care about
  - **Clashes:** software they build on has rules that conflict with their choice
- **Today's help doesn't fit each project**
  - Online quizzes give the same few generic answers to everyone
  - Checking tools only find problems *after* the work is done
  - Lawyers are accurate, but too slow and expensive for students and small teams
- **AI chatbots explain well, but can be confidently wrong**
  - They sound sure even when they're mistaken, and you can't easily check them
  - With legal rules, a confident wrong answer is worse than no answer

---

## 2b. Real-Life Examples
**1 · A start-up shares its code, but wants improvements back**
- They let other companies use their tool for free, as long as those companies share any improvements
- **The risk:** they pick a popular license that doesn't require this, so a big company improves it and keeps the changes
- **With LicenseWise:** they describe their goal in plain words → the tool recommends a license that does require sharing, quotes the exact sentence that says so, and shows whether that sentence was checked

**2 · A small team about to sell an app**
- Their app is built on a free component whose license says: *anything built with me must use my rules too*
- **The risk:** they release under their own terms, and the clash is discovered after launch
- **With LicenseWise:** they upload their list of components → the tool spots the conflict before release, warns about any component it can't identify, and recommends licenses that fit — with proof that selling the app is still allowed

---

## 3. Who · What · When · Where · Why · How
| | |
|---|---|
| **Who** | Developers, students, small teams |
| **What** | Recommends 3 licenses + verified, clause-cited explanations |
| **When** | Starting a project · adding/auditing dependencies |
| **Where** | Web app; Python & npm projects; jurisdiction-neutral |
| **Why** | Faster, understandable, checkable license choice |
| **How** | LLM recommends & explains → NLI model checks each claim against the license text |

---

## 3b. Research Questions
- **RQ1** How well can an open-weight LLM recommend licenses that satisfy a developer's stated requirements?
- **RQ2** How reliably can an NLI model verify LLM claims about license text?
- **RQ3** How faithful are the pipeline's explanations, and does verification change what users see?

---

## 4. Requirements Elicitation
- Instructor feedback: *evaluation is hard; no domain expert; scope it*
  → split into tasks with public ground truth
- Brainstormed within team: inputs, outputs, trust
- Peer groups we joined: **[TEAM]**
- Peer review of our project: **6 points** → 3 already covered · 2 new requirements · 2 showed v1 vs v2 needed clearer explanation
- Outcome: narrowed scope, added verification + disclaimer, **FR10 CLI · FR11 warnings · NFR security**

---

## 4b. Peer Review — What It Changed
| Peer point | Our answer | Outcome |
|---|---|---|
| What triggers warnings? | Unknown/conflicting deps, unverifiable text, unverified claims, vague input | **New FR11:** also warn on API quota/timeout, low NLI confidence |
| CLI commands? | `recommend.py --description · --manifest · --json · --no-verify` | ✅ Covered → **FR10** |
| Malicious / wrong files? | Only 3 manifest types; parsed, never executed | **New NFR:** size/encoding limits, prompt-injection safe |
| Prompt template static? | Fixed, versioned prompts; catalogue built from KB; strict JSON schema | ✅ Covered |
| Legal disclaimer? | In UI, CLI and API output | ✅ Covered |
| RAG data sources? | v1 uses keyword clause retrieval, not RAG; KB = choosealicense + SPDX | Clarified **v1 vs v2** (RAG → Phase 2) |

---

## 5. Functional Requirements
*(insert `docs/figures/13_functional_requirements.png` — replaces the list)*
- Also from peer review (slide 4b): **FR10** command-line interface · **FR11** warnings for API quota / timeout and low-confidence verification
---

## 5b. How FR5, FR6 and FR7 Work Together
*(insert `docs/figures/12_fr5_fr7_flow.png`)*
- **FR7 Flag** — dependency licenses are looked up; a GPL-3.0-only dependency (pyqt5) **constrains** the choice; an unlisted package is flagged **unknown**, never guessed
- **FR5 Explain** — each recommended license gets plain-language claims, each **citing a clause** and quoting it word for word
- **FR6 Verify** — quote must exist in the clause → NLI checks clause ⟹ claim → **Verified / Unverified / Contradicted** badge
- Chain: FR7 shapes the recommendation → FR5 explains it → FR6 checks every claim

---

## 6. Non-Functional Requirements
- **Faithfulness** — never mark a false claim "verified" (target precision ≥ 0.9)
- **Transparency** — every claim links to its source clause
- **Safety** — "not legal advice" disclaimer
- **Latency** — < 5 min on free tier (target < 1 min paid)
- **Cost** — runs on free tier + local NLI model
- **Privacy** — manifests not stored; only package names sent to registries
- **Reproducibility** — seeded, versioned data & scripts
- **Maintainability** — modular pipeline, swappable models
- **Security & robustness** — file type/size/encoding limits; inputs treated as untrusted (prompt injection) *(peer review)*

---

## 7. Top 5 Requirements + User Stories
1. **FR1/FR2 Input** — *As a developer, I describe my project or upload my manifest, so I don't need to know license terms.*
2. **FR4 Recommend** — *…I get 3 ranked licenses that fit my needs.*
3. **FR5 Explain** — *…I see why, in plain language.*
4. **FR6 Verify** — *…I can tell which claims the license text actually supports.*
5. **NFR Faithfulness** — *…I can trust "verified" means verified.*

---

## 8. Use Case: Get a Recommendation
1. User enters description and/or uploads manifest
2. System looks up dependency licenses
3. LLM infers requirements → top 3 licenses
4. LLM writes claims quoting license clauses
5. NLI model labels each claim
6. User reviews cards, opens evidence, reads disclaimer
- **Alt:** vague input → clarifying questions · unknown dependency → warning

---

## 9. System Design
*(insert `docs/system_design.png`)*
- Web UI → FastAPI (job queue, cache) → pipeline
- 2 LLM calls (Groq) + 1 local NLI model
- Offline: data prep + evaluation harness

---

## 10. UI Mock-up
- **Input:** tabs *Describe* / *Upload manifest*
- **Dependencies:** table with license + status badge
- **Results:** 3 cards — license, reason, claims with badges
- **Evidence:** click a claim → highlighted clause
- **Footer:** disclaimer · progress while job runs
*(screenshot / sketch here)*

---

## 11. What Changed Since the Proposal (and Why)
| Proposal | Now | Why |
|---|---|---|
| Full neuro-symbolic design (rules engine, RAG) | **v1: LLM + NLI**; rules engine → Phase 2 | Deliver a working, testable core first |
| RAG over a vector store | **Keyword clause retrieval** from local KB | Simpler, deterministic; RAG → Phase 2 |
| Hosted LLM (Claude) | **Open-weight via Groq** (gpt-oss-120b) | Free tier, open models |
| Whole license text to LLM | **Relevant clauses only** | GPL > 8k tokens/min free-tier limit |
| Repo scanning (ScanCode) | **Registry metadata** (PyPI/npm) | Simpler, fast enough for v1 |
| — | **Software Heritage dataset** added | Real-world license data for EDA |
| ~40 licenses | **34** (software + OSI-approved) | Clear, data-backed scope |
| — | **Hand-labelled NLI test set** | Measure the verifier itself |

---

## 12. Data Overview — Where Everything Comes From
| # | Source | What it is | What we took | Used for | Used live? |
|---|---|---|---|---|---|
| 1 | **Software Heritage license dataset** (Zenodo 6379164) | Archive of 6.5M license files from public code (GitHub, GitLab, Debian, PyPI, npm…) | 5 metadata tables + a 20,000-file text sample | Exploratory analysis, scope check | No |
| 2 | **choosealicense.com** (GitHub repo) | 47 licenses, each with labels + full text | Labels (permissions / conditions / limitations) + text | Knowledge base · **ground truth** | Yes |
| 3 | **SPDX License List** v3.29.0 | Official list of 740 license IDs | ID + "OSI-approved" flag | Scope filter · ID normalisation | Yes |
| 4 | **PyPI / npm registries** | Package metadata | Each dependency's declared license | Manifest input (FR3) | Yes |
| 5 | **Generated test data** | Built by us from sources 2–3 | Requirement profiles, descriptions, clause–claim pairs | Evaluation (RQ1, RQ2) | No |
- Planned, not used yet: **OSADL compatibility matrix** (Phase 2)
- Principle: every label comes from public, curated data — no expert opinion needed

---

## 12a. Source 1 — Software Heritage License Dataset
| File | Rows | Key | Fields | Used? |
|---|---|---|---|---|
| `license-blobs.csv` | 6,482,294 | sha1 ↔ swhid | swhid, sha1, file name | ✅ bridge between keys |
| `blobs-fileinfo.csv` | 6,008,466 | sha1 | mime type, encoding, lines, words, size | ✅ |
| `blobs-scancode.csv` | 7,568,531 detections (4.29M files, 1,705 license IDs) | sha1 | detected SPDX license, confidence 0–100 | ✅ |
| `blobs-earliest.csv` | 5,752,308 | swhid | first commit, date, # commits containing it | ✅ |
| `blobs-origins.csv` | 5,700,334 | swhid | one example repository URL | ✅ |
| `blobs-sample20k.tar.zst` | 20,000 files (30 MB) | sha1 (file name) | the actual license texts | ✅ |
| `blobs.tar.zst` | 6.5M files (**14 GB**) | sha1 | all license texts | ❌ not downloaded |
- Licenses detected by **ScanCode** (industry license scanner); each file deduplicated by its SHA1 hash
- Why the 20k sample: random, representative, small enough to process on a laptop

---

## 12b. Merging the Software Heritage Tables
1. Start from the **20,000 sample files** (file name = SHA1 hash)
2. `license-blobs` → add **Software Heritage ID** + all **file names** (`LICENSE`, `COPYING`, …)
3. `fileinfo` → add **type, encoding, line / word count, size** (joined on SHA1)
4. `scancode` → add **detected licenses + confidence** (joined on SHA1; a file can have several)
5. `earliest` → add **first-seen date + popularity** (joined on Software Heritage ID)
6. `origins` → add **example repository URL** (joined on Software Heritage ID)
- Big tables are **streamed** and filtered to the sample → low memory
- Result: **20,000 rows × 16 columns** (`sample20k_index.csv`)
- Match rate: 100% for IDs and file info · 96% have a date · 95% have an origin URL

---

## 12c. Classifying Each Sample File
| Category | Rule | Files |
|---|---|---|
| **Clean** | exactly one license, in our scope, confidence = 100 | 10,436 (52%) |
| **Variant** | one in-scope license, confidence < 100 (likely modified) | 1,299 (6%) |
| **Multi** | several different licenses detected in one file | 1,687 (8%) |
| **Out of scope** | only licenses outside our 34 | 890 (4%) |
| **Undetected** | no license found (mostly `AUTHORS` files, HTML pages) | 5,688 (28%) |
- **93.8%** of files with a detected license use one of our 34 → scope covers real-world use
- License IDs normalised before comparing: `GPL-3.0-only`, `GPL-3.0-or-later` → `GPL-3.0`
- Use: exploratory analysis only — not used as ground truth

---

## 12d. Source 2 — choosealicense.com (the Knowledge Base)
- 47 files, each = **YAML header + full license text**
- **Kept:** `spdx-id` · `title` · `nickname` · `description` · `hidden` · **`permissions`** · **`conditions`** · **`limitations`** · full text
- **Stripped:** `how` (install instructions) · `note` · `using` (example projects) · `redirect_from` · `featured` (website-only)
- **Label vocabulary** (the ground-truth "facts" about each license)
  - **Permissions (5):** commercial use · modifications · distribution · private use · patent use
  - **Conditions (8):** include copyright · include copyright (source) · document changes · disclose source · same license · same license (file) · same license (library) · network use = distribution
  - **Limitations (4):** no liability · no warranty · no trademark rights · no patent rights
- Output: `licenses.json` (one record per license)

---

## 12e. Source 3 — SPDX License List
- 740 licenses; fields: `licenseId` · `name` · `isOsiApproved` · `isDeprecatedLicenseId` · `reference` · `detailsUrl` · `seeAlso` · `referenceNumber`
- **Kept:** `licenseId`, `isOsiApproved` · **Stripped:** everything else
- Uses:
  - **OSI flag** → keep only Open Source Initiative-approved licenses
  - **ID list** (`spdx_ids.json`) → recognise valid license IDs in dependency metadata
- Older choosealicense IDs (`GPL-3.0`) matched to SPDX (`GPL-3.0-only`) automatically

---

## 12f. Scoping the Knowledge Base: 47 → 34 Licenses
| Step | Removed | Count |
|---|---|---|
| Start | — | **47** |
| Not for software | CC-BY-4.0, CC-BY-SA-4.0 (media) · GFDL-1.3 (docs) · ODbL-1.0 (data) · OFL-1.1 (fonts) · CERN-OHL-P/S/W-2.0 (hardware) | −8 → 39 |
| Not OSI-approved | BSD-3-Clause-Clear · BSD-4-Clause · CC0-1.0 · Vim · WTFPL | −5 → **34** |
- **Language check:** share of common French words per paragraph → **CeCILL-2.1 is French-only** → stays recommendable, but its claims can't be verified (verifier is English-only)
- **Copyleft class** computed from labels: *same license* → strong (9) · *same license (file / library)* → weak (4) · neither → permissive (21)

---

## 12g. Source 4 — PyPI / npm (Dependency Licenses)
- **Manifest parsing** (never executed, only read)
  - `requirements.txt`: package names; skips comments, `-r` / `-e` options, URLs
  - `pyproject.toml`: `[project] dependencies`
  - `package.json`: `dependencies` only — `devDependencies` are not shipped, so ignored
- **Lookup** (in parallel): PyPI JSON API · npm registry
  - PyPI fields read, in order: `license_expression` → `license` → `classifiers`
  - npm field: `license` (text or old `{type: …}` format)
- **Normalisation to SPDX:** exact ID match · 41 common spellings (`GPL v3` → `GPL-3.0-only`, `Apache Software License` → `Apache-2.0`) · expressions kept (`MIT OR Apache-2.0`)
- **Not guessed:** full license text pasted in the field, generic classifiers ("OSI Approved"), missing package → **unknown**

---

## 12h. Splitting Licenses into Clauses
1. Split each license text at blank lines → paragraphs; tidy spacing
2. **Drop non-English paragraphs** (French detector)
3. **Merge short headings** (< 80 characters) into the paragraph below
4. **Lead-in sentences:** a paragraph ending in `:` is attached to **each list item** under it
   - e.g. "Licensor grants You a license … to do the following:" + "b) to translate, adapt, alter, transform, **modify** …"
   - Fixes clauses that stopped at a colon and lost their meaning
5. If no list follows, the lead-in joins the next paragraph
- Result: **812 clauses** from 33 English licenses · median **329 characters** · longest 1,985
- Every clause fits the verifier's 512-token input → nothing truncated

---

## 12i. Finding the Clause for Each Label
- Goal: for "GPL-3.0 has *disclose source*", find **the** clause that says it
- Each of 16 labels has two text patterns
  - **Anchor** (precise): e.g. *"Limitation of Liability"*, *"Grant of Patent License"*, *"prominent notices stating"*
  - **Keywords** (broad): e.g. *liab*, *patent*, *source code*
- Rank clauses by: anchor matches → keyword matches → earliest position
- Checked by hand on MIT, BSD, Apache-2.0, GPL-3.0, MPL-2.0 (e.g. liability → GPL §16, not §17)
- **23** label–license combinations with no matching clause (mostly *commercial use*: BSD never says "sell")
- Used twice: building the verifier test set · choosing evidence for Stage 2

---

## 12j. Ground Truth 1 — Requirement Profiles (for RQ1)
| Requirement | Possible values | Rule over the labels |
|---|---|---|
| Share changes | none · file/library · whole project | copyleft class |
| Network use | must trigger sharing · must not | has / lacks *network use = distribution* |
| Patent grant | required | has *patent use* permission |
| Trademark | protected | has *no trademark rights* |
| Attribution | not required | no *include copyright* condition |
| Document changes | not required | no *document changes* condition |
- All combinations: 192 → **77 profiles** with at least one constraint and at least one correct license
- **Correct answer** = every in-scope license satisfying **all** constraints (computed, not judged)
- Correct licenses per profile: 1 to 29 (median 3) · 1–5 constraints per profile

---

## 12k. Ground Truth 1 — Natural-Language Descriptions
1. **Write:** Qwen3.8-27B turns each profile into ~3 first-person descriptions, each a different persona (student, start-up, researcher…), never naming a license
2. **Check (round trip):** gpt-oss-20b reads each description *without seeing the profile* and recovers the requirements
3. **Keep** only exact matches
- **235 written → 190 kept (81%)** covering 70 of 77 profiles
- Hardest to express: weak copyleft and "network use must not trigger sharing" → 7 profiles with no valid description
- Writer and checker are different from the pipeline model (gpt-oss-120b) → less bias
- Evaluated so far: **104 descriptions, all 70 profiles** (free-tier limit: 200k tokens/day)

---

## 12l. Ground Truth 2 — Clause–Claim Pairs (for RQ2)
- For each license (33) × label it has, take its clause (12i) and build 3 pairs:
| Pair | Claim | Correct answer |
|---|---|---|
| True | "The software is provided without any warranty." | **entailment** |
| Negated | "The software comes with a warranty." | **contradiction** |
| Off-topic | a true claim about a topic the clause never mentions | **neutral** |
- 16 claim templates (true + negated); *private use* left out (never stated in one clause)
- **729 pairs** = 243 entailment + 243 contradiction + 243 neutral
- Labels are automatic → checked by humans (next slide)

---

## 12m. Checking the Automatic Labels by Hand
1. **Sample:** 150 pairs, 50 per label, random with a fixed seed
2. **Label:** two annotators, 75 each; rule = "judge from this clause only, not from what you know about the license"
3. **Settle:** 22 disagreements reviewed by the team → 3 left ambiguous and excluded → **146 labelled pairs**
4. **Clause fix:** 127 labels carried over (96 unchanged, 31 only gained a lead-in) · 23 changed pairs relabelled
5. **Agreement:** 40 pairs labelled by both annotators → **κ = 0.88** (39 pairs; first label visible)
- Automatic labels match final human labels on **97.9%** → the 729-pair set is trustworthy

---

## 12n. What We Left Out — and Why
| Left out | Why |
|---|---|
| 6.5M full license texts (14 GB) | 20k random sample is enough for analysis |
| Undetected & out-of-scope sample files | Not licenses we can recommend |
| 13 of 47 licenses | Not software, or not OSI-approved |
| choosealicense `how` / `note` / `using` fields; most SPDX fields | Website content, not license facts |
| *Private use* label | Never stated in a single clause → can't be verified |
| CeCILL-2.1 in the verifier test set | French text, English-only verifier |
| `devDependencies` | Not shipped with the product |
| 45 descriptions failing the round trip | Text didn't express exactly the profile |
| 86 valid descriptions not yet evaluated | Daily token limit on the free tier |
| OSADL compatibility matrix | Phase 2 (manifest evaluation) |

---

## 13. Data Pipeline at a Glance
1. **Collect:** Software Heritage (6 files) · choosealicense (47) · SPDX (740) · registries (live)
2. **Merge:** 20k sample ⨝ 5 metadata tables → 20,000 × 16 index → analysis
3. **Scope:** 47 → 34 licenses (software + OSI) · CeCILL flagged French
4. **Split:** 33 English licenses → 812 clauses
5. **Ground truth for RQ1:** labels → 77 profiles → 235 descriptions → 190 validated → 104 evaluated
6. **Ground truth for RQ2:** clauses + labels → 729 pairs → 150 hand-checked → 146 labelled (κ 0.88)
7. **At run time:** knowledge base + clauses + registry lookups feed the pipeline

---

## 14. EDA — Software Heritage Sample (20k files)
- **52%** clean single license · **28%** undetected · **15%** variant/multi
- **93.8%** of detected files fall in our 34-license scope
- **MIT 70.5%** · BSD-3 6.9% · Apache-2.0 6.2% · GPL-2.0 4.6% · GPL-3.0 4.1%
- **488** distinct license IDs → long tail
- ScanCode confidence: mean 99.1; **87.9%** score 100
- Median file: **169 words**; 98% text formats
- Median first appearance **2017**; 76% since 2015
- → Fig. A1

---

## 15. EDA — Knowledge Base & Test Data
- Most common conditions (34 licenses): include-copyright 29 · disclose-source 14 · document-changes 14 · same-license 9 · network clause 5
- Copyleft classes: 21 permissive · 4 weak · 9 strong
- Clauses: median 329 chars (fits NLI 512-token limit)
- **77** requirement profiles; correct-answer set size: median 3
- **190** validated descriptions (median 78 words)
- **Insight:** permissive licenses dominate real use → recommendation must still separate subtle copyleft cases
- → Fig. A2

---

## 16. Models & Why
| Model | Role | Why |
|---|---|---|
| **gpt-oss-120b** (Groq) | Stage 1 recommend · Stage 2 explain | Open-weight, strong reasoning, strict JSON output |
| **DeBERTa-v3-large-NLI** (local) | Verifier | Best in our test (beats RoBERTa by +8.7 macro-F1) |
| Qwen3.8-27B | Writes test descriptions | Different family from the pipeline → less bias |
| gpt-oss-20b | Checks test descriptions | Independent round-trip validation |
- Decisions: exactly 3 recommendations · clause-level evidence · retry once if > 50% claims fail
- No fine-tuning in Phase 1

---

## 17. Methodology & Evaluation by RQ
| | Method | Ground truth | Metrics |
|---|---|---|---|
| **RQ1** Recommendation | gpt-oss-120b (Stage 1) on project descriptions written by Qwen, checked by gpt-oss-20b | 77 requirement profiles → correct licenses computed from choosealicense labels | Hit@1 · Hit@3 · Precision@3 · violation rate per requirement |
| **RQ2** Verifier | DeBERTa-v3-large vs RoBERTa-large on clause–claim pairs | 729 auto-labelled pairs · 146 hand-labelled (κ = 0.88) | Accuracy · per-class P / R / F1 · **entailment precision** |
| **RQ3** Faithfulness | Run full pipeline; compare with LLM-only baseline (`--no-verify`) | License text itself (cited clause) | % quotes found verbatim · % claims verified / unverified / contradicted |
- Ground truth = public data, not expert opinion
- Manifest compatibility (OSADL matrix) → Phase 2
---

## 18. Results — RQ2: NLI Verifier (146 hand-labelled pairs)
| | RoBERTa-large | **DeBERTa-v3-large** |
|---|---|---|
| Accuracy | 0.733 | **0.815** |
| Macro-F1 | 0.729 | **0.816** |
| Entailment precision / recall | 0.900 / 0.551 | **0.944 / 0.694** |
| Contradiction F1 | 0.849 | **0.889** |
- Test set: 729 auto-labelled pairs; auto labels **97.9%** correct vs humans
- Annotator agreement **κ = 0.88** (39 rows; first label visible)
- → Fig. A3

---

## 18b. RQ2 — Where the Verifier Struggles
- Confirms ≥ 84% of true claims on distribution, liability, document-changes
- Only 21–25% on commercial use, same-license, network clause
- Cause: claim needs inference beyond the clause's wording ("sell" ≠ "commercial")
- Phase 2 fix: phrase claims in license wording · tune threshold · fine-tune
- → Fig. A3

---

## 19. Results — RQ1: Stage 1 Recommendation
| Correct licenses per description | n | Hit@1 | Hit@3 | Precision@3 |
|---|---|---|---|---|
| **All** | 104 | **0.56** | **0.74** | 0.55 |
| 1–3 (hardest) | 47 | 0.40 | 0.60 | 0.42 |
| 4–10 | 35 | 0.54 | 0.77 | 0.51 |
| > 10 (easiest) | 22 | 0.91 | 1.00 | 0.88 |
- 104 descriptions covering all 70 profiles (free-tier limit: 200k tokens/day)
- Easy requests: near-perfect · specific requests: correct top-3 only **60%**
- Most broken: **trademark 54%** · no-documentation 39% · copyleft level 21% · network 12%
- Over-defaults to **Apache-2.0** (top pick 30×) even when it breaks a requirement
- → Fig. A4


---

## 20. Demo Examples — RQ3 (preliminary)
- **"SaaS library, improvements must come back"** → AGPL-3.0 · GPL-3.0 · MPL-2.0 · **6/10 claims verified**
- **Clinic app + PyQt5 (GPL-3.0) dependency** → found the GPL constraint → GPL-3.0 · AGPL-3.0 · EPL-2.0 · **5/9 verified**, 1 contradicted
- RQ3 so far (2 runs, 19 claims): **100%** quotes found verbatim · **58%** verified · 37% unverified · 5% contradicted
- Full RQ3 batch vs LLM-only baseline → Phase 2
- Runtime 1–5 min (free-tier rate limits)
- Full walkthrough: `notebooks/phase1_results.ipynb` (submitted as the demo)

---

## 21. Strengths & Weaknesses
**Strengths**
- Correct license in top 3 for 74% of descriptions (100% for broad requests)
- "Verified" is reliable (precision 0.94)
- Every claim is traceable to a clause
- Open-weight, free to run; reproducible data
**Weaknesses**
- LLM-only recommendation fails specific requests (Hit@3 0.60 when only 1–3 licenses fit)
- Misses ~30% of true claims (copyleft, "commercial use" wording) → Fig. A3
- LLM alone can pick incompatible licenses (EPL-2.0 example)
- Occasional false "contradicted"
- Slow on free tier; French CeCILL can't be verified

---

## 22. Next Steps (Phase 2)
- Rules engine (v2): check Stage 1 picks against stated requirements & dependency compatibility (26% of descriptions get no correct license today)
- Manifest evaluation with OSADL compatibility ground truth
- Build FastAPI backend + web UI
- Tune NLI threshold / fine-tune on license pairs
- Small user study on explanation clarity

---

## 23. Individual Contributions **[TEAM]**
- [Name] — …
- [Name] — …
- [Name] — …

---

# Figures

## A1. Data — Software Heritage Sample (supports slide 14)
| Figure | Takeaway |
|---|---|
| `01_sample_categories.png` | 52% clean single license · 28% no license detected |
| `02_top_licenses.png` | MIT dominates; 93.8% of detected files are in scope |
| `03_length_and_year.png` | Median file 169 words · most files first seen after 2015 |

---

## A2. Data — Knowledge Base & Test Data (supports slide 15)
| Figure | Takeaway |
|---|---|
| `04_kb_labels_heatmap.png` | 34 licenses × permissions / conditions / limitations; copyleft groups stand out |
| `05_clause_lengths.png` | Every clause fits the NLI model's 512-token input |
| `06_test_descriptions.png` | 190 of 235 descriptions pass the round trip; most have only 1–3 correct licenses |

---

## A3. RQ2 — NLI Verifier (supports slides 18, 18b)
| Figure | Takeaway |
|---|---|
| `07_nli_models.png` | DeBERTa beats RoBERTa on every metric (accuracy 0.82 vs 0.73) |
| `08_nli_confusion.png` | Half the errors (14 of 27) are true claims read as neutral |
| `09_nli_recall_by_label.png` | Strong on liability / distribution; weak on commercial use, copyleft, network clause |

---

## A4. RQ1 — Stage 1 Recommendation (supports slide 19)
| Figure | Takeaway |
|---|---|
| `10_stage1_hits.png` | Hit@3 1.00 for broad requests, 0.60 when only 1–3 licenses fit |
| `11_stage1_violations.png` | Trademark (54%) and no-documentation (39%) requirements broken most often |
