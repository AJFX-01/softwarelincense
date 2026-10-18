"""Evaluate off-the-shelf NLI models on the license claim/clause pairs.

Runs each model over data/processed/nli/pairs.jsonl and scores it against:
  - the automatic labels (all 738 pairs), and
  - the team's hand labels in review_labelled.csv (rows where human_label is filled).

Outputs (data/processed/nli/):
    predictions_<model>.jsonl   per-pair prediction and class probabilities
    nli_results.json            metrics per model and gold set

Usage:
    .venv/bin/python scripts/run_nli.py
    .venv/bin/python scripts/run_nli.py --score-only   # re-score saved predictions (e.g. after hand labelling)
"""

import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NLI_DIR = ROOT / "data" / "processed" / "nli"
PAIRS = NLI_DIR / "pairs.jsonl"
REVIEW = NLI_DIR / "review_labelled.csv"  # team hand labels; build_nli_pairs.py never writes this
ADJUDICATED = NLI_DIR / "disagreements_adjudicated.csv"  # team-settled labels for auto/human disagreements
RELABELLED = NLI_DIR / "relabel_labelled.csv"  # hand labels for pairs changed by the clause fix
RESULTS = NLI_DIR / "nli_results.json"

MODELS = {
    "roberta-large-mnli": "FacebookAI/roberta-large-mnli",
    "deberta-v3-large-nli": "MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli",
}
LABELS = ("entailment", "neutral", "contradiction")
BATCH_SIZE = 16


def predict(model_name, pairs):
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name).to(device).eval()
    id2label = {i: name.lower() for i, name in model.config.id2label.items()}

    predictions = []
    for start in range(0, len(pairs), BATCH_SIZE):
        batch = pairs[start:start + BATCH_SIZE]
        inputs = tokenizer([p["premise"] for p in batch], [p["hypothesis"] for p in batch],
                           truncation="only_first", max_length=512, padding=True,
                           return_tensors="pt").to(device)
        with torch.no_grad():
            probs = torch.softmax(model(**inputs).logits, dim=-1).cpu().tolist()
        for pair, row in zip(batch, probs):
            scores = {id2label[i]: round(p, 4) for i, p in enumerate(row)}
            predictions.append({"pair_id": pair["pair_id"],
                                "predicted": max(scores, key=scores.get), "probs": scores})
        print(f"  {min(start + BATCH_SIZE, len(pairs))}/{len(pairs)}", end="\r", flush=True)
    print()
    return predictions


def metrics(gold, predicted):
    """Accuracy, per-class precision/recall/F1, macro F1, confusion matrix (gold -> predicted)."""
    confusion = {g: {p: 0 for p in LABELS} for g in LABELS}
    for g, p in zip(gold, predicted):
        confusion[g][p] += 1
    per_class = {}
    for label in LABELS:
        tp = confusion[label][label]
        predicted_n = sum(confusion[g][label] for g in LABELS)
        gold_n = sum(confusion[label].values())
        precision = tp / predicted_n if predicted_n else 0.0
        recall = tp / gold_n if gold_n else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_class[label] = {"precision": round(precision, 3), "recall": round(recall, 3),
                            "f1": round(f1, 3), "support": gold_n}
    return {
        "n": len(gold),
        "accuracy": round(sum(g == p for g, p in zip(gold, predicted)) / len(gold), 3),
        "macro_f1": round(sum(c["f1"] for c in per_class.values()) / len(LABELS), 3),
        "per_class": per_class,
        "confusion": confusion,
    }


def read_labels(path, column):
    with open(path, newline="", encoding="utf-8") as f:
        return {row["pair_id"]: row[column].strip().lower() for row in csv.DictReader(f)}


def human_labels():
    """Hand labels, with adjudicated disagreements applied.

    A disagreement left without a final_label (still ambiguous after review) is
    dropped rather than guessed.
    """
    if not REVIEW.exists():
        return {}
    labels = read_labels(REVIEW, "human_label")
    if RELABELLED.exists():
        labels.update(read_labels(RELABELLED, "human_label"))
    if ADJUDICATED.exists():
        labels.update(read_labels(ADJUDICATED, "final_label"))
    return {pair_id: label for pair_id, label in labels.items() if label in LABELS}


def report(name, m):
    print(f"  {name}: n={m['n']}  accuracy={m['accuracy']}  macro-F1={m['macro_f1']}")
    for label, c in m["per_class"].items():
        print(f"    {label:13} P={c['precision']:.3f} R={c['recall']:.3f} F1={c['f1']:.3f} (n={c['support']})")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--score-only", action="store_true")
    args = parser.parse_args()

    pairs = [json.loads(line) for line in PAIRS.read_text().splitlines() if line]
    auto = {p["pair_id"]: p["nli_label"] for p in pairs}
    human = human_labels()
    results = {}

    for short, model_name in MODELS.items():
        out = NLI_DIR / f"predictions_{short}.jsonl"
        if args.score_only:
            predictions = [json.loads(line) for line in out.read_text().splitlines() if line]
        else:
            print(f"\n{short} ({model_name})")
            predictions = predict(model_name, pairs)
            out.write_text("".join(json.dumps(p) + "\n" for p in predictions))
        predicted = {p["pair_id"]: p["predicted"] for p in predictions}

        results[short] = {"auto": metrics([auto[i] for i in auto], [predicted[i] for i in auto])}
        if human:
            ids = sorted(human)
            results[short]["human"] = metrics([human[i] for i in ids], [predicted[i] for i in ids])

        print(f"\n== {short}")
        for gold_name, m in results[short].items():
            report(f"vs {gold_name} labels", m)

    if human:
        agree = sum(human[i] == auto[i] for i in human)
        results["auto_label_accuracy_vs_human"] = {"n": len(human), "agreement": round(agree / len(human), 3)}
        print(f"\nauto labels agree with human labels on {agree}/{len(human)} reviewed pairs")

    RESULTS.write_text(json.dumps(results, indent=2))
    print(f"\nwrote {RESULTS.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
