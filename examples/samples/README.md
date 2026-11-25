# Data samples

Each file here is a small sample of one kind of data LicenseWise uses. Every sample is
copied from the real data files, not written by hand. Each file starts with an `_about`
field that explains what it is and why it looks the way it does.

To make the files easy to read, every long text (a description, a license, a prompt) is
stored as a list of short lines. In the real data files each one is a single string.

| File | What it shows | Copied from |
|---|---|---|
| `01_license_choosealicense.json` | One license (MIT) with its choosealicense.com labels and full text | `data/processed/licenses.json` |
| `02_requirements.json` | Every requirement a profile can contain, and the label rule behind each | `scripts/build_scenarios.py` |
| `03_profile.json` | Profile P005: its requirements and the correct licenses computed from the labels | `data/processed/scenarios/profiles.jsonl` |
| `04_personas.json` | The three personas used for P005, plus others | `data/processed/scenarios/descriptions.jsonl` |
| `05_description.json` | Description P005-013 (startup founder) and its validation check | `data/processed/scenarios/descriptions.jsonl` |
| `06_stage1_phase1_vs_phase2.json` | The same description run with the Phase 1 prompt (no labels) and the Phase 2 prompt (with labels) | `data/processed/scenarios/stage1_results*.jsonl` |
| `07_clause_claim_pairs.json` | One MIT clause and its three pairs, plus a pair that people corrected | `data/processed/nli/pairs.jsonl`, `review_labelled.csv` |
| `08_claim_in_the_app.json` | A claim from a real run, before and after the verifier | `data/processed/runs/demo_saas.json` |

The files follow one test case from start to finish: requirements (02) are grouped into
a profile (03), and a persona (04) writes a description (05) from it. Stage 1 then picks
licenses for that description (06), Stage 2 explains each license with claims, and the
verifier checks each claim against its clause (07, 08).

The same examples appear on the appendix slides A2 to A5.

To rebuild the samples after the data changes, run this from the project root:

```bash
.venv/bin/python -m scripts.build_examples
```
