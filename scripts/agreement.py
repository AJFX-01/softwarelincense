"""Inter-annotator agreement on the round-1 NLI review sample.

Round 1: reviewer A labelled sheet rows 2-76, reviewer B rows 77-151 (75 each).
For agreement, each reviewer relabelled 20 of the other's rows:
    agreement_reviewerA.csv  A's second labels on B's rows 77-96
    agreement_reviewerB.csv  B's second labels on A's rows 2-21
Both files have the first reviewer's `human_label` and the new `second_label`.

Reports raw agreement and Cohen's kappa (chance-corrected), overall and per
direction. Rows where either label is missing or "unclear" are left out.

Output: data/processed/nli/agreement_results.json
"""

import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NLI_DIR = ROOT / "data" / "processed" / "nli"
SHEETS = {"B relabels A's rows": NLI_DIR / "agreement" / "agreement_reviewerB.csv",
          "A relabels B's rows": NLI_DIR / "agreement" / "agreement_reviewerA.csv"}
LABELS = ("entailment", "neutral", "contradiction")


def pairs(path):
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    out = []
    for r in rows:
        first, second = r["human_label"].strip().lower(), r["second_label"].strip().lower()
        if first in LABELS and second in LABELS:
            out.append((r["pair_id"], first, second))
    return out, len(rows)


def cohen_kappa(items):
    n = len(items)
    observed = sum(a == b for _, a, b in items) / n
    first, second = Counter(a for _, a, _ in items), Counter(b for _, _, b in items)
    expected = sum(first[l] * second[l] for l in LABELS) / (n * n)
    return observed, (observed - expected) / (1 - expected) if expected < 1 else 1.0


def confusion(items):
    table = {a: {b: 0 for b in LABELS} for a in LABELS}
    for _, a, b in items:
        table[a][b] += 1
    return table


def main():
    results, everything = {}, []
    for name, path in SHEETS.items():
        items, total = pairs(path)
        everything += items
        observed, kappa = cohen_kappa(items)
        results[name] = {"rows": total, "scored": len(items), "agreement": round(observed, 3),
                         "kappa": round(kappa, 3),
                         "disagreements": [{"pair_id": i, "first": a, "second": b}
                                           for i, a, b in items if a != b]}
    observed, kappa = cohen_kappa(everything)
    results["overall"] = {"scored": len(everything), "agreement": round(observed, 3),
                          "kappa": round(kappa, 3), "confusion_first_vs_second": confusion(everything)}
    (NLI_DIR / "agreement_results.json").write_text(json.dumps(results, indent=2))

    for name, r in results.items():
        print(f"{name}: n={r['scored']}  agreement={r['agreement']}  kappa={r['kappa']}")
    print("\nconfusion (rows = first label, columns = second label):")
    print(f"{'':15}" + "".join(f"{l:>15}" for l in LABELS))
    for a, row in results["overall"]["confusion_first_vs_second"].items():
        print(f"{a:15}" + "".join(f"{row[b]:>15}" for b in LABELS))


if __name__ == "__main__":
    main()
