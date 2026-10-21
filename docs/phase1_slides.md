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
*(insert `docs/figures/14_data_sources.png`)*
- Four public sources → what we took → what each one feeds
- Knowledge base and dependency check are used live; analysis and ground truth are built offline

---

## 12a. Software Heritage — Tables Used and How They Were Merged
*(insert `docs/figures/15_software_heritage_merge.png`)*
- Start from the 20,000-file text sample; join five metadata tables onto it
- Two keys: SHA1 (file content) and Software Heritage ID — `license-blobs` links them
- Result: one 20,000 × 16 table; the 14 GB full-text archive was not needed
- **Why we need it:** exploratory analysis of real-world licenses (slides 14, A1) · evidence that our 34-license scope covers 93.8% of real use · a pool of modified ("variant") licenses for Phase 2 robustness tests
- **Not used for:** the pipeline at run time or the ground truth

---

## 12b. Classifying Each Sample File
*(insert `docs/figures/16_sample_categories.png`)*
- Four yes/no questions sort every file into one of five groups
- 93.8% of files with a license use one of our 34 → our scope matches real-world use
- Used for analysis only, not as ground truth

---

## 12c. choosealicense.com & SPDX — the Knowledge Base
- **choosealicense.com:** 47 licenses, each = labels + full text
  - **Permissions (5):** commercial use · modifications · distribution · private use · patent use
  - **Conditions (8):** include copyright · include copyright (source) · document changes · disclose source · same license · same license (file) · same license (library) · network use = distribution
  - **Limitations (4):** no liability · no warranty · no trademark rights · no patent rights
- **SPDX:** 740 official license IDs → used to keep only OSI-approved licenses and to recognise valid IDs
- Which fields were kept or dropped → slide 12j

---

## 12d. Scoping the Knowledge Base: 47 → 34
*(insert `docs/figures/17_scope_funnel.png`)*
- Remove licenses not meant for software (8), then those not OSI-approved (5)
- Each remaining license is classed permissive, weak or strong copyleft from its labels
- CeCILL-2.1 is French-only → recommended, but its claims can't be verified

---

## 12e. PyPI / npm — Dependency Licenses
- **Reading the manifest** (never executed)
  - `requirements.txt` → package names · `pyproject.toml` → `[project] dependencies` · `package.json` → `dependencies` (dev-only packages ignored)
- **Looking up each package** on PyPI or npm, in parallel
  - PyPI: license expression → license field → classifiers · npm: license field
- **Turning it into an SPDX ID:** exact match · 41 common spellings (`GPL v3` → `GPL-3.0-only`) · combined licenses kept (`MIT OR Apache-2.0`)
- **Never guessed:** pasted license text, vague labels, missing packages → **unknown**

---

## 12f. From License Text to Clauses
*(insert `docs/figures/18_clauses.png`)*
- **Why split into clauses?**
  - The verifier reads at most **512 tokens (~2,000 characters)**; GPL-3.0 alone is **35,000 characters**
  - A claim must be checked against **the one passage that supports it**, not a whole license
  - Groq's free tier allows **8,000 tokens per minute**, so Stage 2 can only receive the relevant clauses
  - Users need a **specific passage** to read as evidence (FR9)
- Five steps → 812 clauses from 33 English licenses; attaching lead-ins fixes clauses that stopped at a colon
- **What the clauses feed:** Stage 2 (numbered clauses the LLM must quote) → verifier (clause = premise) → evidence drawer in the UI → verifier test set (RQ2)

---

## 12g. RQ1 Part A — Building Requirement Profiles and Their Correct Answers
*(insert `docs/figures/19a_rq1_profiles.png`)*

**The idea:** before we can test whether the system picks the right license, we need questions where we already know the right answer.

1. **Choose what developers might ask for.** Each license comes with labels saying what it allows and requires. We picked the 6 that actually differ between licenses — e.g. "changes must be shared", "contributors grant patent rights", "users don't need to credit us".
2. **Try every combination.** For each requirement, a developer picks one setting or doesn't care:
   - "Share changes" has 4 settings: nothing · just the changed files · the whole project · don't care
   - "Network use" has 3: online use must trigger sharing · must not · don't care
   - The other four have 2 each: wanted · don't care
   - 4 × 3 × 2 × 2 × 2 × 2 = **192** possible requests (not 2⁶ = 64, because two requirements have more than yes/no)
3. **Drop the empty one.** "I don't care about anything" isn't a real request → 191 left.
4. **Work out which licenses fit.** For each request, we check all 34 licenses against their labels. If no license can satisfy everything (114 requests), the request is dropped. If at least one can (77 requests), it's kept.
5. **The result: 77 profiles.** Each profile is a request plus the list of licenses that fit it. That list is the **answer key** — worked out from the labels, not guessed by a person.

---

## 12h. RQ1 Part B — Realistic Descriptions, Then Testing Stage 1
*(insert `docs/figures/19b_rq1_descriptions_eval.png`)*

**The idea:** real developers don't write lists of requirements — they describe their project in their own words. So we turn each profile into everyday descriptions and see if the system can still find the right licenses.

6. **Write.** One AI model (Qwen) writes about 3 short descriptions per profile, each in a different voice (a student, a start-up founder, a researcher…), without mentioning any license. → 235 descriptions
7. **Check.** A second, different AI model reads each description *without* seeing the profile and lists the requirements it can spot.
8. **Keep only clear descriptions.** If the checker spots exactly the profile's requirements, the description is clear enough to keep. → 190 kept, 45 dropped
9. **Test Stage 1.** Our system reads only the description and recommends 3 licenses. We compare its picks with the answer key from Part A. → 104 tested, covering all 70 profiles

**How we score it**
- **Hit@1:** the first pick is a correct license · **Hit@3:** at least one of the three is correct · **Precision@3:** how many of the three are correct
- **Why 104 and not 190?** The free AI service limits how much text we can send per day, so we tested one description per profile first — every profile is covered.
- Results → slide 19

---

## 12i. Ground Truth for RQ2 — Clause–Claim Pairs & Human Check
*(insert `docs/figures/20_ground_truth_rq2.png`)*
- Every clause gives three pairs with known answers: true · negated · off-topic
- **Where the 16 templates come from:** a template is a pair of sentences we wrote for one license label — a true version and its opposite (e.g. "provided without any warranty" / "comes with a warranty")
  - choosealicense has 17 labels; we wrote one for each except *private use*, which no license states in a single clause → 16
- **Where 243 each comes from:**
  - 33 English licenses × the labels each one has = 266 license–label combinations
  - minus 23 where no matching clause was found (mostly "commercial use": BSD never says "sell") = **243 clauses**
  - each clause makes exactly one true, one negated and one off-topic pair → 243 × 3 = **729 pairs**
- 150 checked by hand → automatic answers 97.9% correct; annotators agree (κ = 0.88)

---

## 12j. What We Kept and What We Left Out
*(insert `docs/figures/21_kept_vs_left_out.png`)*
- Every exclusion has a reason: not needed, not verifiable, or out of scope
- Phase 2 adds the OSADL compatibility matrix

---

## 13. Data Pipeline at a Glance
1. **Collect:** Software Heritage · choosealicense · SPDX · registries (live)
2. **Merge:** 20k sample + 5 tables → one 20,000-row table → analysis
3. **Scope:** 47 → 34 licenses · CeCILL flagged French
4. **Split:** 33 English licenses → 812 clauses
5. **RQ1 ground truth:** 77 profiles → 190 validated descriptions → 104 evaluated
6. **RQ2 ground truth:** 729 pairs → 150 hand-checked → 146 labelled
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
