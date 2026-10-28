"""Check each Stage 2 claim against the clause it cites.

1. Quote check: the quote must appear in the cited clause (ignoring case,
   whitespace and quote-mark style). Otherwise the claim is "unverified".
2. Entailment check: DeBERTa NLI with the cited clause as premise and the claim
   as hypothesis -> entailment = "verified", contradiction = "contradicted",
   neutral = "unverified". The premise is the whole clause, matching how the
   verifier was evaluated (data/processed/nli/).
"""

import re
from functools import cache

NLI_MODEL = "MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli"
STATUS = {"entailment": "verified", "contradiction": "contradicted", "neutral": "unverified"}


def _norm(text):
    text = text.lower().translate(str.maketrans({"“": '"', "”": '"', "‘": "'", "’": "'"}))
    return re.sub(r"\s+", " ", text).strip().strip('."\'')


@cache
def _model():
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    tokenizer = AutoTokenizer.from_pretrained(NLI_MODEL)
    model = AutoModelForSequenceClassification.from_pretrained(NLI_MODEL).to(device).eval()
    return tokenizer, model, device


def load():
    """Load the NLI model now instead of on the first claim (about 1.7 GB)."""
    _model()


def _nli(pairs):
    import torch

    tokenizer, model, device = _model()
    inputs = tokenizer([p for p, _ in pairs], [h for _, h in pairs], truncation="only_first",
                       max_length=512, padding=True, return_tensors="pt").to(device)
    with torch.no_grad():
        probs = torch.softmax(model(**inputs).logits, dim=-1).cpu().tolist()
    labels = {i: name.lower() for i, name in model.config.id2label.items()}
    return [{labels[i]: round(p, 3) for i, p in enumerate(row)} for row in probs]


def verify(claims, clauses_by_id):
    """Add quote_found, status and nli probabilities to each claim (in place); return claims."""
    to_check = []
    for claim in claims:
        clause = clauses_by_id.get(claim["clause_id"])
        claim["quote_found"] = bool(clause) and _norm(claim["quote"]) in _norm(clause)
        if not claim["quote_found"]:
            claim["status"] = "unverified"
            claim["reason"] = "cited clause not found" if not clause else "quote not found in cited clause"
            claim["nli"] = None
        else:
            to_check.append((claim, clause))
    if to_check:
        premise_hypothesis = [(clause, claim["text"]) for claim, clause in to_check]
        for (claim, _), probs in zip(to_check, _nli(premise_hypothesis)):
            label = max(probs, key=probs.get)
            claim["status"] = STATUS[label]
            claim["reason"] = f"NLI: {label} ({probs[label]:.2f})"
            claim["nli"] = probs
    return claims
