from licensewise import verifier

CLAUSE = "Permission is hereby granted, free of charge, to any person obtaining a copy of this software."


def test_quote_check_and_nli_mapping(monkeypatch):
    # The NLI model is mocked: entailment for the first checked claim, contradiction for the second.
    outputs = iter([[{"entailment": 0.9, "neutral": 0.08, "contradiction": 0.02},
                     {"entailment": 0.1, "neutral": 0.2, "contradiction": 0.7}]])
    monkeypatch.setattr(verifier, "_nli", lambda pairs: next(outputs))
    claims = [
        {"text": "Anyone may use it for free.", "quote": "free of charge", "clause_id": "c1"},
        {"text": "You must pay a fee.", "quote": "“FREE   of charge”", "clause_id": "c1"},  # style-insensitive
        {"text": "x", "quote": "not in the clause", "clause_id": "c1"},
        {"text": "y", "quote": "free", "clause_id": "missing"},
    ]
    verifier.verify(claims, {"c1": CLAUSE})
    assert [c["status"] for c in claims] == ["verified", "contradicted", "unverified", "unverified"]
    assert claims[2]["reason"] == "quote not found in cited clause"
    assert claims[3]["reason"] == "cited clause not found"
    assert claims[2]["nli"] is None
