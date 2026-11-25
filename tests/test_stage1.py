from licensewise import llm, stage1


def fake_llm(answers, calls):
    """complete_json stand-in returning the given recommendation lists in turn."""
    def complete_json(model, system, user, output):
        calls.append({"system": system, "user": user})
        ids = answers[min(len(calls) - 1, len(answers) - 1)]
        return output.model_validate({
            "requirements": [{"text": "permissive", "source": "description"}],
            "recommendations": [{"spdx_id": i, "reason": "fits"} for i in ids],
            "conflicts": [], "clarifying_questions": ["a?", "b?", "c?"]})
    return complete_json


def test_recommend_returns_three_and_caps_questions(monkeypatch):
    calls = []
    monkeypatch.setattr(llm, "complete_json", fake_llm([["MIT", "Apache-2.0", "BSD-3-Clause"]], calls))
    out = stage1.recommend("a small CLI tool")
    assert [r["spdx_id"] for r in out["recommendations"]] == ["MIT", "Apache-2.0", "BSD-3-Clause"]
    assert len(out["clarifying_questions"]) == 2
    assert len(calls) == 1


def test_duplicate_ids_trigger_one_retry(monkeypatch):
    calls = []
    monkeypatch.setattr(llm, "complete_json",
                        fake_llm([["MIT", "MIT", "Apache-2.0"], ["MIT", "Apache-2.0", "ISC"]], calls))
    out = stage1.recommend("a small CLI tool")
    assert [r["spdx_id"] for r in out["recommendations"]] == ["MIT", "Apache-2.0", "ISC"]
    assert len(calls) == 2 and "DIFFERENT" in calls[1]["user"]


def test_v2_prompt_sends_labels(monkeypatch):
    calls = []
    monkeypatch.setattr(llm, "complete_json", fake_llm([["MIT", "Apache-2.0", "ISC"]], calls))
    stage1.recommend("x", variant="v1")
    stage1.recommend("x", variant="v2")
    assert "[permissions:" not in calls[0]["user"] and "[permissions:" in calls[1]["user"]
    assert calls[1]["system"].startswith(calls[0]["system"]) and len(calls[1]["system"]) > len(calls[0]["system"])


def test_needs_some_input():
    import pytest
    with pytest.raises(ValueError):
        stage1.recommend(None, None)
