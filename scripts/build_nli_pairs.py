"""Build (clause, claim, label) pairs for testing the NLI verifier.

For every in-scope license and every choosealicense label it carries
(e.g. disclose-source, warranty), we:
  1. find the license clause that expresses the label (licensewise.clauses),
  2. pair it with a true claim about that label   -> entailment,
  3. pair it with the negated claim               -> contradiction,
  4. pair a true claim about a *different* label
     with this clause, when the clause does not
     mention that other topic                     -> neutral.

The labels are automatic, so clause retrieval can be wrong; a stratified sample
is hand-checked by the team.

Round 1 hand labels (data/processed/nli/round1/) are carried over to pairs whose
license, premise and claim are unchanged. Sampled pairs that no longer exist
are replaced with new pairs, written to relabel_sample.csv for labelling.

Outputs (data/processed/nli/):
    pairs.jsonl           all pairs
    review_labelled.csv   carried-over hand labels (final labels after adjudication)
    relabel_sample.csv    replacement pairs to hand-label (empty `human_label`)
    retrieval_misses.csv  (license, label) combinations where no clause was found
"""

import csv
import json
import random
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from licensewise.clauses import LABEL_PATTERNS, best_clause, clauses, mentions  # noqa: E402

KB = ROOT / "data" / "processed" / "licenses.json"
OUT_DIR = ROOT / "data" / "processed" / "nli"
ROUND1 = OUT_DIR / "round1"

SEED = 621
REVIEW_PER_LABEL = 50  # per NLI label -> 150 rows reviewed
NLI_LABELS = ("entailment", "contradiction", "neutral")
REVIEW_FIELDS = ["pair_id", "license", "label", "premise", "hypothesis", "auto_label",
                 "human_label", "notes"]

# (category, label) -> (true claim, negated claim)
# private-use is left out: licenses rarely state it in a single clause.
CLAIMS = {
    ("permissions", "commercial-use"): (
        "The software may be used or sold for commercial purposes.",
        "The software may not be used or sold for commercial purposes."),
    ("permissions", "modifications"): (
        "You are allowed to modify the software.",
        "You are not allowed to modify the software."),
    ("permissions", "distribution"): (
        "You are allowed to distribute copies of the software.",
        "You are not allowed to distribute copies of the software."),
    ("permissions", "patent-use"): (
        "Contributors grant you a license to their patents that cover the software.",
        "Contributors do not grant you any rights to their patents."),
    ("conditions", "include-copyright"): (
        "You must keep the copyright and license notices when you distribute the software.",
        "You do not need to keep the copyright and license notices when you distribute the software."),
    ("conditions", "include-copyright--source"): (
        "Copies of the source code must keep the copyright and license notices.",
        "Copies of the source code do not need to keep the copyright and license notices."),
    ("conditions", "document-changes"): (
        "If you modify the files, you must state that you changed them.",
        "If you modify the files, you do not need to state that you changed them."),
    ("conditions", "disclose-source"): (
        "When you distribute the software, you must make its source code available.",
        "You may distribute the software without making its source code available."),
    ("conditions", "network-use-disclose"): (
        "If users interact with the software over a network, you must offer them its source code.",
        "Letting users interact with the software over a network never requires sharing its source code."),
    ("conditions", "same-license"): (
        "Modified versions you distribute must be licensed under the same license.",
        "You may distribute modified versions under any license you choose."),
    ("conditions", "same-license--file"): (
        "Modified files from the project must stay under the same license.",
        "Modified files from the project may be released under any license."),
    ("conditions", "same-license--library"): (
        "Modifications to the library must be released under the same license.",
        "Modifications to the library may be released under any license."),
    ("limitations", "liability"): (
        "The authors are not liable for damages caused by the software.",
        "The authors are liable for damages caused by the software."),
    ("limitations", "warranty"): (
        "The software is provided without any warranty.",
        "The software comes with a warranty."),
    ("limitations", "trademark-use"): (
        "The license does not grant rights to use the contributors' trademarks.",
        "The license grants you the right to use the contributors' trademarks."),
    ("limitations", "patent-use"): (
        "The license does not grant you any patent rights.",
        "The license grants you patent rights from the contributors."),
}
assert CLAIMS.keys() == LABEL_PATTERNS.keys()


def round1_neutral_topics():
    """(license, category, label) -> topic of the neutral claim used in round 1."""
    path = ROUND1 / "pairs.jsonl"
    if not path.exists():
        return {}
    topics = {}
    for line in path.read_text().splitlines():
        p = json.loads(line)
        if p["nli_label"] == "neutral":
            topics[(p["license"], p["category"], p["label"])] = p["hypothesis_topic"]
    return topics


def build_pairs(licenses):
    previous_topics = round1_neutral_topics()
    pairs, misses = [], []
    for lic in licenses:
        paras = clauses(lic["text"])
        found = {}
        for (category, label), (true_claim, false_claim) in CLAIMS.items():
            if label not in lic[category]:
                continue
            clause = best_clause(paras, (category, label))
            if clause is None:
                misses.append({"license": lic["spdx_id"], "category": category, "label": label})
                continue
            found[(category, label)] = clause
            base = {"license": lic["spdx_id"], "category": category, "label": label, "premise": clause}
            pairs.append({**base, "hypothesis": true_claim, "nli_label": "entailment"})
            pairs.append({**base, "hypothesis": false_claim, "nli_label": "contradiction"})

        # Neutral: a true claim about another topic, on a clause that never mentions it.
        for key, clause in found.items():
            others = [k for k in CLAIMS if k != key and k[1] != key[1] and not mentions(clause, k)]
            if not others:
                continue
            # Keep round 1's claim when it is still valid, so reviewed pairs stay stable;
            # otherwise pick with a per-pair seed (independent of the other licenses).
            topic = previous_topics.get((lic["spdx_id"], *key))
            reuse = [k for k in others if k[1] == topic]
            other = reuse[0] if reuse else random.Random(f"{SEED}:{lic['spdx_id']}:{key}").choice(others)
            pairs.append({"license": lic["spdx_id"], "category": key[0], "label": key[1],
                          "premise": clause, "hypothesis": CLAIMS[other][0],
                          "hypothesis_topic": other[1], "nli_label": "neutral"})

    for i, p in enumerate(pairs, 1):
        p["pair_id"] = f"N{i:04d}"
    return pairs, misses


def round1_final_labels():
    """Round-1 rows keyed by (license, premise, hypothesis) -> (auto label, final label or '')."""
    review = ROUND1 / "review_labelled.csv"
    if not review.exists():
        return {}
    with open(review, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    adjudicated = {}
    adjudicated_file = ROUND1 / "disagreements_adjudicated.csv"
    if adjudicated_file.exists():
        with open(adjudicated_file, newline="", encoding="utf-8") as f:
            adjudicated = {r["pair_id"]: r["final_label"].strip().lower() for r in csv.DictReader(f)}
    labels = {}
    for r in rows:
        final = adjudicated.get(r["pair_id"], r["human_label"].strip().lower())
        labels[(r["license"], r["premise"], r["hypothesis"])] = (r["auto_label"], final, r["notes"])
    return labels


def write_csv(path, fieldnames, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main():
    rng = random.Random(SEED)  # only used to sample replacement pairs
    # Non-English texts (CeCILL-2.1 is French) are skipped: the NLI models are English-only.
    licenses = [l for l in json.loads(KB.read_text()) if l["in_scope"] and l["language"] == "en"]
    pairs, misses = build_pairs(licenses)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUT_DIR / "pairs.jsonl", "w", encoding="utf-8") as f:
        for p in pairs:
            f.write(json.dumps(p) + "\n")
    write_csv(OUT_DIR / "retrieval_misses.csv", ["license", "category", "label"], misses)

    print(f"{len(pairs)} pairs from {len(licenses)} licenses")
    for label, n in Counter(p["nli_label"] for p in pairs).most_common():
        print(f"  {label:13} {n}")
    print(f"{len(misses)} (license, label) combinations with no matching clause")

    # Carry round-1 labels to unchanged pairs; replace the rest with new pairs.
    old = round1_final_labels()
    carried, kept_per_label, carried_ids = [], Counter(), set()
    for p in pairs:
        hit = old.get((p["license"], p["premise"], p["hypothesis"]))
        how = "unchanged"
        if hit is None:
            # Same claim, and the round-1 clause is contained in the new one: the only
            # change is the lead-in sentence now attached to a list item.
            # A round-1 clause ending in ':' was truncated (the bug being fixed), so its
            # label does not transfer.
            hit = next((v for (lic, prem, hyp), v in old.items()
                        if lic == p["license"] and hyp == p["hypothesis"]
                        and not prem.endswith(":") and prem in p["premise"]), None)
            how = "lead-in added"
        if hit is None:
            continue
        kept_per_label[p["nli_label"]] += 1
        carried_ids.add(p["pair_id"])
        _auto, final, notes = hit
        carried.append({**p, "auto_label": p["nli_label"], "human_label": final,
                        "notes": notes, "carried": how})

    new_pairs = [p for p in pairs if p["pair_id"] not in carried_ids]
    # Prefer the new versions of reviewed pairs that changed (same license and claim),
    # so the relabelling checks the clause fix directly; fill the rest at random.
    changed = {(lic, hyp) for (lic, _prem, hyp) in old}
    relabel = []
    for label in NLI_LABELS:
        need = max(0, REVIEW_PER_LABEL - kept_per_label[label])
        pool = [p for p in new_pairs if p["nli_label"] == label]
        preferred = [p for p in pool if (p["license"], p["hypothesis"]) in changed]
        rest = [p for p in pool if (p["license"], p["hypothesis"]) not in changed]
        picked = preferred[:need]
        relabel += picked + rng.sample(rest, min(need - len(picked), len(rest)))
    rng.shuffle(relabel)

    write_csv(OUT_DIR / "review_labelled.csv", REVIEW_FIELDS + ["carried"], carried)
    write_csv(OUT_DIR / "relabel_sample.csv", REVIEW_FIELDS,
              [{**p, "auto_label": p["nli_label"], "human_label": "", "notes": ""} for p in relabel])

    print(f"\nround-1 reviewed pairs carried over: {len(carried)} of {len(old)} "
          f"({dict(kept_per_label)}); {dict(Counter(c['carried'] for c in carried))}")
    print(f"replacement pairs to label: {len(relabel)} -> relabel_sample.csv")


if __name__ == "__main__":
    main()
