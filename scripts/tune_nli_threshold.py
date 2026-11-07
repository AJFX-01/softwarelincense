"""Phase 2: tune the verifier's entailment threshold.

Phase 1 took the class with the highest probability. Here a claim is
"verified" when P(entailment) >= t; otherwise it gets the larger of neutral and
contradiction. A lower t confirms more true claims (recall) at the risk of
confirming wrong ones (precision).

t is chosen on the pairs WITHOUT human labels (automatic labels), as the value
with the best macro-F1 among those keeping entailment precision >= MIN_PRECISION.
It is then reported on the 146 human-labelled pairs, which play no part in the
choice.

Usage:
    .venv/bin/python scripts/tune_nli_threshold.py                      # baseline DeBERTa
    .venv/bin/python scripts/tune_nli_threshold.py --predictions data/processed/nli/finetune/oof_<config>.jsonl
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from run_nli import NLI_DIR, PAIRS, ROOT, human_labels, metrics  # noqa: E402

MIN_PRECISION = 0.90  # a wrong "verified" costs more than a missing one
THRESHOLDS = [round(0.05 * i, 2) for i in range(1, 20)]


def decide(probs, t):
    if probs["entailment"] >= t:
        return "entailment"
    return "neutral" if probs["neutral"] >= probs["contradiction"] else "contradiction"


def score(ids, gold, probs, t):
    return metrics([gold[i] for i in ids], [decide(probs[i], t) for i in ids])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", default=str(NLI_DIR / "predictions_deberta-v3-large-nli.jsonl"))
    args = parser.parse_args()

    path = Path(args.predictions).resolve()
    probs = {p["pair_id"]: p["probs"] for p in map(json.loads, path.read_text().splitlines())}
    auto = {p["pair_id"]: p["nli_label"] for p in map(json.loads, PAIRS.read_text().splitlines())}
    human = human_labels()
    tune_ids = sorted(set(auto) - set(human))
    test_ids = sorted(human)

    curve = []
    print(f"{'t':>5} {'tune P(ent)':>11} {'R(ent)':>7} {'macroF1':>8}")
    for t in THRESHOLDS:
        m = score(tune_ids, auto, probs, t)
        e = m["per_class"]["entailment"]
        curve.append({"t": t, "entailment_precision": e["precision"], "entailment_recall": e["recall"],
                      "macro_f1": m["macro_f1"], "accuracy": m["accuracy"]})
        print(f"{t:5.2f} {e['precision']:11.3f} {e['recall']:7.3f} {m['macro_f1']:8.3f}")

    ok = [c for c in curve if c["entailment_precision"] >= MIN_PRECISION]
    best = max(ok, key=lambda c: (c["macro_f1"], c["t"]))["t"]
    argmax_test = metrics([human[i] for i in test_ids],
                          [max(probs[i], key=probs[i].get) for i in test_ids])
    tuned_test = score(test_ids, human, probs, best)

    print(f"\nchosen t = {best} (tuning pairs: n={len(tune_ids)})")
    for name, m in (("argmax (Phase 1)", argmax_test), (f"t = {best}", tuned_test)):
        e = m["per_class"]["entailment"]
        print(f"  human test n={m['n']}  {name:17} acc={m['accuracy']} macroF1={m['macro_f1']} "
              f"P(ent)={e['precision']} R(ent)={e['recall']}")

    out = path.with_name(f"threshold_{path.stem}.json")
    out.write_text(json.dumps({"predictions": str(path.relative_to(ROOT)), "min_precision": MIN_PRECISION,
                               "chosen_t": best, "curve_on_tuning_pairs": curve,
                               "human_test": {"argmax": argmax_test, "tuned": tuned_test}}, indent=2))
    print(f"wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
