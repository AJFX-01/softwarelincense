"""v1 pipeline: description and/or manifest -> 3 licenses with verified claims."""

import time

from licensewise import deps, kb, llm, stage1, stage2, verifier

RETRY_IF_FAILED_SHARE = 0.5  # re-run Stage 2 once if more than half the claims fail


def recommend(description=None, manifest=None, model=llm.PIPELINE_MODEL, verify=True, progress=None):
    """`progress(step, detail)` is called as each step starts (used by the API to report status)."""
    report = progress or (lambda step, detail=None: None)
    timings, started = {}, time.perf_counter()

    report("dependencies", "Looking up dependency licenses" if manifest else "No manifest")
    dependencies = deps.dependency_licenses(manifest) if manifest else []
    timings["dependency_lookup_s"] = round(time.perf_counter() - started, 1)

    report("stage1")
    t = time.perf_counter()
    s1 = stage1.recommend(description, dependencies, model=model)
    timings["stage1_s"] = round(time.perf_counter() - t, 1)

    t = time.perf_counter()
    recommendations = []
    for rank, rec in enumerate(s1["recommendations"], 1):
        lic = kb.licenses()[rec["spdx_id"]]
        entry = {"rank": rank, "spdx_id": rec["spdx_id"], "title": lic["title"],
                 "reason": rec["reason"], "claims": [], "note": None}
        if lic["language"] != "en":
            entry["note"] = (f"The license text is in '{lic['language']}'; the English NLI "
                             "verifier cannot check claims about it, so none are shown.")
            recommendations.append(entry)
            continue
        report("retrieval", f"{rec['spdx_id']} ({rank}/3)")
        report("explain", f"{rec['spdx_id']} ({rank}/3)")
        clauses_by_id, claims = stage2.explain(rec["spdx_id"], s1["requirements"], model=model)
        if verify:
            report("verify", f"{rec['spdx_id']} ({rank}/3)")
            verifier.verify(claims, clauses_by_id)
            failed = [c for c in claims if c["status"] != "verified"]
            if claims and len(failed) / len(claims) > RETRY_IF_FAILED_SHARE:
                report("explain", f"{rec['spdx_id']}: regenerating after failed verification")
                feedback = [f"{c['text']} (cited {c['clause_id']}: {c['reason']})" for c in failed]
                _, retry = stage2.explain(rec["spdx_id"], s1["requirements"], model=model,
                                          feedback=feedback)
                verifier.verify(retry, clauses_by_id)
                if sum(c["status"] == "verified" for c in retry) > len(claims) - len(failed):
                    claims = retry
                    entry["note"] = "Explanation regenerated once after failed verification."
        for c in claims:
            c["clause_text"] = clauses_by_id.get(c["clause_id"])
        entry["claims"] = claims
        recommendations.append(entry)
    report("response")
    timings["stage2_and_verify_s"] = round(time.perf_counter() - t, 1)
    timings["total_s"] = round(time.perf_counter() - started, 1)

    return {
        "input": {"description": description, "manifest": str(manifest) if manifest else None},
        "model": model,
        "dependencies": [{**d, "in_catalogue": kb.kb_id(d["license"]) is not None}
                         for d in dependencies],
        **{k: s1[k] for k in ("requirements", "conflicts", "clarifying_questions")},
        "recommendations": recommendations,
        "usage": dict(llm.USAGE),
        "timings": timings,
        "disclaimer": "Explanations are based on license text only. This is not legal advice.",
    }
