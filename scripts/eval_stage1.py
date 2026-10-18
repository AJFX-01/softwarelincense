"""Evaluate Stage 1 (requirements -> top-3 licenses) on the validated descriptions.

For each description that passed the round trip, run Stage 1 on the text alone
and compare its 3 recommendations with the profile's gold set (every in-scope
license that satisfies all of the profile's constraints).

Metrics:
    Hit@1         top recommendation is in the gold set
    Hit@3         at least one of the 3 is in the gold set
    Precision@3   share of the 3 recommendations that are in the gold set
    Violation     share of the 3 recommendations that break at least one stated constraint
                  (same as 1 - Precision@3, reported per constraint as well)

Results are appended to data/processed/scenarios/stage1_results.jsonl, so the
script can be re-run to resume. --score-only prints metrics from saved results.

Usage:
    .venv/bin/python scripts/eval_stage1.py              # run (about 30 s per description on the free tier)
    .venv/bin/python scripts/eval_stage1.py --score-only
"""

import argparse
import json
import random
import re
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import groq  # noqa: E402

from build_scenarios import DIMENSIONS  # noqa: E402
from licensewise import kb, llm, stage1  # noqa: E402

SCEN = ROOT / "data" / "processed" / "scenarios"
DESCRIPTIONS = SCEN / "descriptions.jsonl"
PROFILES = SCEN / "profiles.jsonl"
RESULTS = SCEN / "stage1_results.jsonl"
SUMMARY = SCEN / "stage1_summary.json"


def bucket(gold_size):
    return "1-3" if gold_size <= 3 else "4-10" if gold_size <= 10 else ">10"


def load_jsonl(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line] if path.exists() else []


def violated_constraints(spdx_id, constraints):
    lic = kb.licenses()[spdx_id]
    return [dim for dim, value in constraints.items() if not DIMENSIONS[dim][value][1](lic)]


def score(results, profiles):
    groups = defaultdict(list)
    for r in results:
        groups["all"].append(r)
        groups[f"gold {bucket(r['gold_size'])}"].append(r)
    summary = {}
    for name, rows in groups.items():
        n = len(rows)
        summary[name] = {
            "n": n,
            "hit@1": round(sum(r["hit@1"] for r in rows) / n, 3),
            "hit@3": round(sum(r["hit@3"] for r in rows) / n, 3),
            "precision@3": round(sum(r["precision@3"] for r in rows) / n, 3),
        }
    per_dim = defaultdict(lambda: [0, 0])  # dimension -> [violating recs, recs where it applied]
    for r in results:
        constraints = profiles[r["profile_id"]]["constraints"]
        for rec in r["recommended"]:
            for dim in constraints:
                per_dim[dim][1] += 1
            for dim in rec["violates"]:
                per_dim[dim][0] += 1
    summary["violation_rate_by_constraint"] = {d: round(v / t, 3) for d, (v, t) in sorted(per_dim.items())}
    return summary


def _recommend_waiting(text, model, wait):
    """stage1.recommend; with wait=True, sleep through Groq's daily-quota (TPD) errors."""
    while True:
        try:
            return stage1.recommend(text, model=model)
        except groq.RateLimitError as e:
            match = re.search(r"try again in (?:(\d+)h)?(?:(\d+)m)?([\d.]+)s", str(e))
            if not wait or not match:
                raise
            h, m, sec = (float(x or 0) for x in match.groups())
            pause = h * 3600 + m * 60 + sec + 15
            print(f"  daily token quota reached; waiting {pause / 60:.0f} min "
                  f"(until {time.strftime('%H:%M', time.localtime(time.time() + pause))})", flush=True)
            time.sleep(pause)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int)
    parser.add_argument("--score-only", action="store_true")
    parser.add_argument("--model", default=llm.PIPELINE_MODEL)
    parser.add_argument("--one-per-profile-first", action="store_true",
                        help="evaluate one description from each uncovered profile before the rest")
    parser.add_argument("--wait", action="store_true",
                        help="sleep through the free-tier daily token quota instead of stopping")
    args = parser.parse_args()

    profiles = {p["profile_id"]: p for p in load_jsonl(PROFILES)}
    descriptions = [d for d in load_jsonl(DESCRIPTIONS) if d["valid"]]
    for i, d in enumerate(descriptions):
        d["desc_id"] = f"{d['profile_id']}-{i:03d}"

    if not args.score_only:
        done = {r["desc_id"] for r in load_jsonl(RESULTS)}
        todo = [d for d in descriptions if d["desc_id"] not in done]
        # Shuffled (fixed seed) so a run cut short by the daily quota is still a mixed sample.
        random.Random(621).shuffle(todo)
        if args.one_per_profile_first:
            # Profiles with no result yet come first (one description each), then the rest.
            covered = {r["profile_id"] for r in load_jsonl(RESULTS)}
            first, rest = [], []
            for d in todo:
                if d["profile_id"] not in covered:
                    covered.add(d["profile_id"])
                    first.append(d)
                else:
                    rest.append(d)
            todo = first + rest
        todo = todo[: args.limit]
        print(f"{len(descriptions)} valid descriptions, {len(done)} done, {len(todo)} to run ({args.model})")
        for i, d in enumerate(todo, 1):
            started = time.perf_counter()
            try:
                out = _recommend_waiting(d["text"], args.model, args.wait)
            except groq.AuthenticationError:
                raise SystemExit("Groq rejected the API key in .env.")
            except groq.RateLimitError as e:
                # Retries are exhausted, so this is the daily quota: stop and resume later.
                print(f"  stopped at {d['desc_id']}: {e}", flush=True)
                break
            except (groq.APIStatusError, groq.APIConnectionError, ValueError) as e:
                print(f"  {d['desc_id']}: skipped ({str(e)[:150]})", flush=True)
                continue
            gold = set(d["gold"])
            constraints = profiles[d["profile_id"]]["constraints"]
            recommended = [{"spdx_id": r["spdx_id"], "in_gold": r["spdx_id"] in gold,
                            "violates": violated_constraints(r["spdx_id"], constraints)}
                           for r in out["recommendations"]]
            ids = [r["spdx_id"] for r in recommended]
            row = {"desc_id": d["desc_id"], "profile_id": d["profile_id"], "model": args.model,
                   "gold_size": len(gold), "recommended": recommended,
                   "hit@1": bool(ids) and ids[0] in gold, "hit@3": any(i in gold for i in ids),
                   "precision@3": sum(i in gold for i in ids) / 3,
                   "requirements": out["requirements"],
                   "clarifying_questions": out["clarifying_questions"],
                   "seconds": round(time.perf_counter() - started, 1)}
            with open(RESULTS, "a", encoding="utf-8") as f:
                f.write(json.dumps(row) + "\n")
            print(f"[{i}/{len(todo)}] {d['desc_id']} gold={len(gold):2} -> {', '.join(ids)}  "
                  f"hit@1={int(row['hit@1'])} hit@3={int(row['hit@3'])}", flush=True)
        print("tokens:", dict(llm.USAGE))

    results = load_jsonl(RESULTS)
    if not results:
        return
    summary = score(results, profiles)
    SUMMARY.write_text(json.dumps(summary, indent=2))
    print(f"\n{'group':12} {'n':>4} {'hit@1':>7} {'hit@3':>7} {'prec@3':>7}")
    for name, m in summary.items():
        if name != "violation_rate_by_constraint":
            print(f"{name:12} {m['n']:>4} {m['hit@1']:>7} {m['hit@3']:>7} {m['precision@3']:>7}")
    print("\nviolation rate by constraint:", summary["violation_rate_by_constraint"])


if __name__ == "__main__":
    main()
