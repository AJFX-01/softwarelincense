"""Write small, readable samples of each kind of data to examples/samples/.

Every sample is copied from the real data files (nothing is made up), with an
"_about" note on what it is and why it looks the way it does. Re-run after the
data changes:  .venv/bin/python -m scripts.build_examples
"""

import csv
import json
import textwrap

from licensewise import DATA, ROOT, kb, stage1

OUT = ROOT / "examples" / "samples"
SCEN = DATA / "scenarios"
NLI = DATA / "nli"
WIDTH = 90  # longest line of text in a sample file
TITLES = {  # shown on the UI's Data samples page
    "01_license_choosealicense.json": "A license from choosealicense.com",
    "02_requirements.json": "Requirements",
    "03_profile.json": "A profile",
    "04_personas.json": "Personas",
    "05_description.json": "A description",
    "06_stage1_phase1_vs_phase2.json": "Stage 1: Phase 1 vs Phase 2 prompt",
    "07_clause_claim_pairs.json": "Clause-claim pairs",
    "08_claim_in_the_app.json": "A claim in the app, before and after verifying",
}

LICENSE = "MIT"
PROFILE = "P005"
DESCRIPTION = "P005-013"     # used on slides A2 and A3
CATALOGUE_LICENSE = "BSD-3-Clause"
PAIR_LICENSE, PAIR_LABEL = "MIT", "warranty"
HUMAN_CORRECTED_PAIR = "N0539"   # built as neutral, people marked it entailment
DEMO_CLAIM_START = "When you share a modified version"


def jsonl(path):
    return [json.loads(line) for line in path.open() if line.strip()]


def readable(value):
    """Turn every long string into a list of short lines, so the JSON reads well in an
    editor. Line breaks in the original text start a new line; an empty string is a blank
    line. To get the original back, join the lines (with a space within a paragraph)."""
    if isinstance(value, dict):
        return {k: readable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [readable(v) for v in value]
    if isinstance(value, str) and (len(value) > WIDTH or "\n" in value):
        lines = []
        for paragraph in value.split("\n"):
            lines.extend(textwrap.wrap(paragraph, WIDTH, break_on_hyphens=False) or [""])
        return lines
    return value


def write(name, data):
    path = OUT / name
    data = {"_title": TITLES[name], **data}
    path.write_text(json.dumps(readable(data), indent=2, ensure_ascii=False) + "\n")
    print("wrote", path.relative_to(ROOT))


def descriptions_with_ids():
    """Same numbering as scripts/eval_stage1.py: valid descriptions, in file order."""
    rows = [d for d in jsonl(SCEN / "descriptions.jsonl") if d["valid"]]
    for i, d in enumerate(rows):
        d["desc_id"] = f"{d['profile_id']}-{i:03d}"
    return rows


def license_sample():
    lic = next(l for l in json.loads((DATA / "licenses.json").read_text()) if l["spdx_id"] == LICENSE)
    write("01_license_choosealicense.json", {
        "_about": "One license as stored in our knowledge base (data/processed/licenses.json, 47 "
                  "licenses, 34 in scope). Title, description, labels and text come from "
                  "choosealicense.com; in_scope and language are ours. The labels (permissions, "
                  "conditions, limitations) are what the profiles' correct answers are computed "
                  "from, and what the Phase 2 prompt shows the LLM.",
        "license": lic,
    })


def requirement_samples():
    from scripts.build_scenarios import DIMENSIONS
    write("02_requirements.json", {
        "_about": "Every requirement a test profile can contain: 6 kinds (dimensions), each with "
                  "one or more values. Each value has a plain sentence (what a developer wants) "
                  "and a rule over a license's labels that decides whether a license meets it. "
                  "A kind left out of a profile means 'don't care'. From scripts/build_scenarios.py.",
        "requirements": [{"kind": dim, "value": value, "sentence": sentence}
                         for dim, values in DIMENSIONS.items()
                         for value, (sentence, _) in values.items()],
    })


def profile_sample():
    profile = next(p for p in jsonl(SCEN / "profiles.jsonl") if p["profile_id"] == PROFILE)
    write("03_profile.json", {
        "_about": "A profile is a set of requirements (77 profiles in "
                  "data/processed/scenarios/profiles.jsonl). 'gold' is the list of correct "
                  "licenses: every in-scope license whose labels meet all the requirements. It is "
                  "computed from the labels, not chosen by a person. Here: trademark protected "
                  "means the license has the 'trademark-use' limitation; document changes not "
                  "required means it lacks the 'document-changes' condition.",
        "profile": profile,
    })


def persona_samples(descriptions):
    mine = [d for d in descriptions if d["profile_id"] == PROFILE]
    all_personas = sorted({d["persona"] for d in descriptions})
    write("04_personas.json", {
        "_about": "A persona is who is 'speaking' in a description. The LLM that writes the "
                  "descriptions must use a different persona and project type for each one of a "
                  "profile, so the same requirements appear in different words (a founder says "
                  "'brand assets', a hobbyist says 'my character names'). This tests that the "
                  "system understands meaning, not keywords. Personas are free text chosen by the "
                  "writing model (qwen3.8-27b), not a fixed list.",
        "personas_for_this_profile": [{"desc_id": d["desc_id"], "persona": d["persona"]} for d in mine],
        "persona_count_all_descriptions": len(all_personas),
        "some_other_personas": all_personas[:12],
    })


def description_sample(descriptions):
    d = next(x for x in descriptions if x["desc_id"] == DESCRIPTION)
    write("05_description.json", {
        "_about": "A test description: the project story LicenseWise reads. It never names a "
                  "license or a label. 'recovered' is what a second, different model "
                  "(gpt-oss-20b) found when it read the story without seeing the profile; it had "
                  "to match the profile's requirements exactly, otherwise the description was "
                  "thrown away ('valid'). 190 of 235 passed. 'gold' is copied from the profile.",
        "description": d,
    })


def phase_comparison():
    v1 = next(r for r in jsonl(SCEN / "stage1_results.jsonl") if r["desc_id"] == DESCRIPTION)
    v2 = next(r for r in jsonl(SCEN / "stage1_results_v2_gpt-oss-120b.jsonl")
              if r["desc_id"] == DESCRIPTION)
    def line(labels):
        return next(row for row in kb.catalogue(labels=labels).splitlines()
                    if row.startswith(f"- {CATALOGUE_LICENSE}:"))

    write("06_stage1_phase1_vs_phase2.json", {
        "_about": f"The same description ({DESCRIPTION}, see 05_description.json) and the same "
                  "model (gpt-oss-120b), run with the Phase 1 prompt (v1) and the Phase 2 prompt "
                  "(v2). The only change in v2: each catalogue line ends with the license's "
                  "labels, and the instructions say to turn each requirement into a label and "
                  "check every pick against it. 'requirements' is what the model wrote down from "
                  "the description; 'recommended' shows each pick, whether it is in the gold list, "
                  "and which requirements it breaks.",
        "catalogue_line": {"phase1_v1": line(False), "phase2_v2": line(True)},
        "system_prompt": {"phase1_v1": stage1.PROMPTS["v1"], "phase2_v2": stage1.PROMPTS["v2"]},
        "result": {"phase1_v1": v1, "phase2_v2": v2},
    })


def pair_samples():
    pairs = [p for p in jsonl(NLI / "pairs.jsonl")
             if p["license"] == PAIR_LICENSE and p["label"] == PAIR_LABEL]
    corrected = next(r for r in csv.DictReader((NLI / "review_labelled.csv").open())
                     if r["pair_id"] == HUMAN_CORRECTED_PAIR)
    write("07_clause_claim_pairs.json", {
        "_about": "Clause-claim pairs train and test the verifier (data/processed/nli/pairs.jsonl, "
                  "729 pairs = 243 clause-label matches x 3). 'premise' is the clause from the "
                  "license that expresses the label; 'hypothesis' is the claim. For each match we "
                  "write three claims from templates, so the right answer is known in advance: "
                  "entailment (a true sentence for this label), contradiction (the same sentence "
                  "made opposite) and neutral (a true sentence for a different label, which this "
                  "clause does not say). Two people checked 146 pairs by hand (97.9% agreed).",
        "pairs_from_one_clause": pairs,
        "_about_human_check": "A pair the people checking corrected (from "
                              "data/processed/nli/review_labelled.csv). It was built as neutral (a "
                              "sentence for a different label), but this clause does say it, so "
                              "the right answer is entailment. 'auto_label' is the verdict from how "
                              "the pair was built; 'human_label' is the checked one, which is used "
                              "for training and testing.",
        "human_corrected_pair": corrected,
    })


def app_claim_sample():
    run = json.loads((DATA / "runs" / "demo_saas.json").read_text())
    for rec in run["recommendations"]:
        for claim in rec["claims"]:
            if claim["text"].startswith(DEMO_CLAIM_START):
                write("08_claim_in_the_app.json", {
                    "_about": "A claim from a real pipeline run (the hosted-SaaS demo, "
                              "data/processed/runs/demo_saas.json). Stage 2 (the LLM) writes "
                              "'text', the 'clause_id' it relies on and an exact 'quote'. Then "
                              "'quote_found' checks the quote really is in that clause, and the "
                              "verifier reads the full 'clause_text' with the claim (a "
                              "clause-claim pair) and gives the 'nli' scores; the highest sets "
                              "'status'. The LLM never grades its own claim.",
                    "license": rec["spdx_id"],
                    "before_verification": {k: claim[k] for k in ("text", "clause_id", "quote")},
                    "after_verification": claim,
                })
                return
    raise SystemExit(f"demo claim not found: {DEMO_CLAIM_START}")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    descriptions = descriptions_with_ids()
    license_sample()
    requirement_samples()
    profile_sample()
    persona_samples(descriptions)
    description_sample(descriptions)
    phase_comparison()
    pair_samples()
    app_claim_sample()


if __name__ == "__main__":
    main()
