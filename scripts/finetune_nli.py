"""Phase 2: fine-tune the DeBERTa verifier on our license clause/claim pairs.

Memory: full fine-tuning of DeBERTa-v3-large needs ~7 GB for AdamW states
alone, more than this 8 GB machine can spare, so only the top K encoder layers
(plus pooler and classifier) are trained; the rest stay as pre-trained. K is a
hyperparameter (K=0 trains the classification head only).
Because the bottom 24-K layers are frozen, their output for each pair never
changes: it is computed once and cached (cache/layer<N>.pt, ~370 MB), and
training runs only the top K layers. This gives the same result as running the
whole model each step, with a fraction of the memory and time.

Evaluation is cross-validated and grouped, so no prediction comes from a model
that saw the same license during training:
  --group license  5 folds by license (main result)
  --group label    5 folds by license label (stress test: the claim templates of
                   a held-out label are never seen, closer to new claim wording)
Each pair gets an out-of-fold prediction. Hyperparameters are compared on the
583 pairs without human labels; the 146 human-labelled pairs are the test set.
Training targets are the human label where one exists, otherwise the automatic one.

Outputs (data/processed/nli/finetune/):
    oof_<config>.jsonl   out-of-fold predictions (same format as run_nli.py)
    results.json         one entry per config: tuning-set and human-test metrics

Usage:
    .venv/bin/python scripts/finetune_nli.py --unfreeze 4 --lr 2e-5 --epochs 3
    .venv/bin/python scripts/finetune_nli.py --unfreeze 4 --final   # train on all pairs, save to models/
"""

import argparse
import gc
import json
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from run_nli import MODELS, NLI_DIR, PAIRS, human_labels, metrics  # noqa: E402

OUT = NLI_DIR / "finetune"
FINAL_DIR = NLI_DIR.parents[2] / "models" / "deberta-v3-large-license-nli"  # gitignored
BASE_MODEL = MODELS["deberta-v3-large-nli"]
FOLDS = 5


def make_folds(pairs, group_key, seed):
    """Assign whole groups to folds, largest first, always to the smallest fold."""
    sizes = {}
    for p in pairs:
        sizes[p[group_key]] = sizes.get(p[group_key], 0) + 1
    groups = sorted(sizes, key=lambda g: (-sizes[g], g))
    random.Random(seed).shuffle(groups)  # break ties between equal-size groups
    groups.sort(key=lambda g: -sizes[g])
    folds, load = {}, [0] * FOLDS
    for g in groups:
        k = load.index(min(load))
        folds[g] = k
        load[k] += sizes[g]
    return [folds[p[group_key]] for p in pairs]


def cache_hidden_states(pairs, layer, tokenizer, device):
    """Output of encoder layer `layer` (1-based; 0 = embeddings) for every pair, on CPU.

    Computed in the checkpoint's float16, exactly as the Phase 1 baseline ran."""
    import torch
    from transformers import AutoModelForSequenceClassification

    path = OUT / "cache" / f"layer{layer}.pt"
    if path.exists():
        return torch.load(path)
    print(f"  caching layer {layer} outputs (one pass of the frozen model)", flush=True)
    model = AutoModelForSequenceClassification.from_pretrained(BASE_MODEL).to(device).eval()
    cache = {}
    for batch in batches(pairs, 16):
        inputs = encode(tokenizer, batch, device)
        with torch.no_grad():
            hidden = model.deberta(**inputs, output_hidden_states=True).hidden_states[layer]
        for pair, h, mask in zip(batch, hidden.cpu(), inputs["attention_mask"].cpu()):
            cache[pair["pair_id"]] = h[: int(mask.sum())].clone()  # drop padding
    del model
    if device == "mps":
        torch.mps.empty_cache()
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(cache, path)
    return cache


class Tail:
    """The trainable top of the model: the last K encoder layers, pooler and classifier."""

    def __init__(self, unfreeze, device):
        import copy

        import torch
        from transformers import AutoModelForSequenceClassification

        full = AutoModelForSequenceClassification.from_pretrained(BASE_MODEL)  # float16 checkpoint
        encoder = full.deberta.encoder
        self.encoder = encoder  # for attention mask / relative-position helpers (frozen)
        self.layers = list(encoder.layer[len(encoder.layer) - unfreeze:]) if unfreeze else []
        self.modules = self.layers + [full.pooler, full.dropout, full.classifier]
        self.id2label = {i: name.lower() for i, name in full.config.id2label.items()}
        encoder.layer = encoder.layer[:0]  # drop the frozen layers' weights
        full.deberta.embeddings = None
        del full
        gc.collect()
        # Trainable weights in float32: AdamW updates in float16 are unstable.
        for m in [encoder] + self.modules:
            m.to(device=device, dtype=torch.float32)
        for param in encoder.parameters():
            param.requires_grad = False
        self.initial = copy.deepcopy([m.state_dict() for m in self.modules])
        self.device = device

    def reset(self):
        for m, state in zip(self.modules, self.initial):
            m.load_state_dict(state)
        for m in self.modules:
            for param in m.parameters():
                param.requires_grad = True

    def parameters(self):
        return [p for m in self.modules for p in m.parameters()]

    def train(self, on=True):
        for m in self.modules:
            m.train(on)

    def __call__(self, hidden, mask):
        attention = self.encoder.get_attention_mask(mask)
        relative_pos = self.encoder.get_rel_pos(hidden)
        rel_embeddings = self.encoder.get_rel_embedding()
        for layer in self.layers:
            hidden, _ = layer(hidden, attention, relative_pos=relative_pos, rel_embeddings=rel_embeddings)
        pooler, dropout, classifier = self.modules[-3:]
        return classifier(dropout(pooler(hidden)))


def batches(items, size, shuffle_seed=None):
    items = list(items)
    if shuffle_seed is not None:
        random.Random(shuffle_seed).shuffle(items)
    for i in range(0, len(items), size):
        yield items[i:i + size]


def encode(tokenizer, batch, device):
    return tokenizer([p["premise"] for p in batch], [p["hypothesis"] for p in batch],
                     truncation="only_first", max_length=512, padding=True,
                     return_tensors="pt").to(device)


def stack(cache, batch, device):
    """Pad cached hidden states of a batch into (hidden, attention mask)."""
    import torch

    length = max(len(cache[p["pair_id"]]) for p in batch)
    hidden = torch.zeros(len(batch), length, cache[batch[0]["pair_id"]].shape[-1])
    mask = torch.zeros(len(batch), length, dtype=torch.long)
    for i, p in enumerate(batch):
        h = cache[p["pair_id"]]
        hidden[i, : len(h)] = h
        mask[i, : len(h)] = 1
    return hidden.to(device), mask.to(device)


def length_batches(cache, pairs, size, seed):
    """Batches of similar-length pairs (less padding, far less memory), in shuffled order."""
    ordered = sorted(pairs, key=lambda p: len(cache[p["pair_id"]]))
    chunks = [ordered[i:i + size] for i in range(0, len(ordered), size)]
    random.Random(seed).shuffle(chunks)
    return chunks


def train_fold(tail, cache, train, args, label_id):
    import torch
    from transformers import get_linear_schedule_with_warmup

    tail.reset()
    params = tail.parameters()
    optimizer = torch.optim.AdamW(params, lr=args.lr, weight_decay=0.01)
    steps = args.epochs * ((len(train) + args.batch - 1) // args.batch)
    scheduler = get_linear_schedule_with_warmup(optimizer, int(0.1 * steps), steps)
    tail.train()
    for epoch in range(args.epochs):
        total, started = 0.0, time.time()
        for step, batch in enumerate(length_batches(cache, train, args.batch, seed=args.seed + epoch), 1):
            hidden, mask = stack(cache, batch, tail.device)
            target = torch.tensor([label_id[p["target"]] for p in batch], device=tail.device)
            loss = torch.nn.functional.cross_entropy(tail(hidden, mask), target)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(params, 1.0)
            optimizer.step()
            scheduler.step()
            optimizer.zero_grad()
            total += loss.item() * len(batch)
            if step % 20 == 0:
                # MPS keeps buffers for every batch shape it has seen; without this its
                # memory grows until the machine swaps (an epoch went from <1 min to 30 min).
                if tail.device == "mps":
                    torch.mps.empty_cache()
                print(f"      step {step}: {time.time() - started:.0f}s", flush=True)
        print(f"    epoch {epoch + 1}: loss {total / len(train):.4f} ({time.time() - started:.0f}s)", flush=True)
    tail.train(False)


def predict(tail, cache, pairs):
    import torch

    out = []
    for batch in batches(pairs, 16):
        with torch.no_grad():
            probs = torch.softmax(tail(*stack(cache, batch, tail.device)), -1).cpu().tolist()
        for pair, row in zip(batch, probs):
            scores = {tail.id2label[i]: round(p, 4) for i, p in enumerate(row)}
            out.append({"pair_id": pair["pair_id"], "predicted": max(scores, key=scores.get), "probs": scores})
    return out


def save_final(tail, cache, pairs, args, label_id, tokenizer, config):
    """Train on all 729 pairs and save a complete model the verifier can load."""
    import torch
    from transformers import AutoModelForSequenceClassification

    print(f"  final model: train {len(pairs)}", flush=True)
    train_fold(tail, cache, pairs, args, label_id)
    full = AutoModelForSequenceClassification.from_pretrained(BASE_MODEL)  # float16, like the verifier
    layers = full.deberta.encoder.layer
    targets = (list(layers[len(layers) - args.unfreeze:]) if args.unfreeze else []) + \
        [full.pooler, full.dropout, full.classifier]
    for target, trained in zip(targets, tail.modules):
        target.load_state_dict({k: v.to(torch.float16).cpu() for k, v in trained.state_dict().items()})
    FINAL_DIR.mkdir(parents=True, exist_ok=True)
    full.save_pretrained(FINAL_DIR)
    tokenizer.save_pretrained(FINAL_DIR)
    (FINAL_DIR / "training.json").write_text(json.dumps(
        {"config": config, **vars(args), "base_model": BASE_MODEL, "pairs": len(pairs),
         "trained_on": "data/processed/nli/pairs.jsonl (human label where available)"}, indent=2))
    print(f"saved {FINAL_DIR}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--unfreeze", type=int, default=4, help="top encoder layers to train (0 = head only)")
    parser.add_argument("--lr", type=float, default=2e-5)
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--group", choices=["license", "label"], default="license")
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--final", action="store_true", help="train on all pairs and save the model")
    args = parser.parse_args()

    import torch
    from transformers import AutoTokenizer

    torch.manual_seed(args.seed)
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)

    pairs = [json.loads(line) for line in PAIRS.read_text().splitlines() if line]
    human = human_labels()
    for p in pairs:
        p["target"] = human.get(p["pair_id"], p["nli_label"])
    fold_of = make_folds(pairs, args.group, args.seed)

    config = f"{args.group}_k{args.unfreeze}_lr{args.lr:g}_e{args.epochs}_b{args.batch}_s{args.seed}"
    print(f"config {config} on {device}", flush=True)
    started = time.time()
    cache = cache_hidden_states(pairs, 24 - args.unfreeze, tokenizer, device)
    tail = Tail(args.unfreeze, device)
    label_id = {name: i for i, name in tail.id2label.items()}
    if args.final:
        return save_final(tail, cache, pairs, args, label_id, tokenizer, config)
    predictions = []
    for k in range(FOLDS):
        train = [p for p, f in zip(pairs, fold_of) if f != k]
        held_out = [p for p, f in zip(pairs, fold_of) if f == k]
        print(f"  fold {k + 1}/{FOLDS}: train {len(train)}, held out {len(held_out)} "
              f"({len({p[args.group] for p in held_out})} {args.group}s)", flush=True)
        train_fold(tail, cache, train, args, label_id)
        predictions += predict(tail, cache, held_out)

    OUT.mkdir(parents=True, exist_ok=True)
    oof = OUT / f"oof_{config}.jsonl"
    oof.write_text("".join(json.dumps(p) + "\n" for p in predictions))

    predicted = {p["pair_id"]: p["predicted"] for p in predictions}
    auto = {p["pair_id"]: p["nli_label"] for p in pairs}
    tune_ids = sorted(set(auto) - set(human))
    test_ids = sorted(human)
    entry = {
        "config": config, **vars(args), "base_model": BASE_MODEL,
        "minutes": round((time.time() - started) / 60, 1),
        "tuning_auto": metrics([auto[i] for i in tune_ids], [predicted[i] for i in tune_ids]),
        "human_test": metrics([human[i] for i in test_ids], [predicted[i] for i in test_ids]),
    }
    results_path = OUT / "results.json"
    results = json.loads(results_path.read_text()) if results_path.exists() else {}
    results[config] = entry
    results_path.write_text(json.dumps(results, indent=2))

    for name in ("tuning_auto", "human_test"):
        m = entry[name]
        e = m["per_class"]["entailment"]
        print(f"  {name:12} n={m['n']} acc={m['accuracy']} macroF1={m['macro_f1']} "
              f"P(ent)={e['precision']} R(ent)={e['recall']}")
    print(f"wrote {oof.name} ({entry['minutes']} min)")


if __name__ == "__main__":
    main()
