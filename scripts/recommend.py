"""Command-line entry point for the v1 pipeline.

Usage:
    .venv/bin/python scripts/recommend.py --description "SaaS analytics library; keep improvements open"
    .venv/bin/python scripts/recommend.py --manifest examples/requirements.txt
    .venv/bin/python scripts/recommend.py --description "..." --manifest package.json --json out.json
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from licensewise import llm, pipeline  # noqa: E402

BADGE = {"verified": "[verified]    ", "unverified": "[unverified]  ", "contradicted": "[contradicted]"}


def show(result):
    if result["dependencies"]:
        print("Dependencies:")
        for d in result["dependencies"]:
            print(f"  {d['name']:30} {d['license'] or 'UNKNOWN (' + d['declared'] + ')'}")
        print()
    print("Requirements understood:")
    for r in result["requirements"]:
        print(f"  - {r['text']} ({r['source']})")
    for c in result["conflicts"]:
        print(f"  ! {c['dependency']} ({c['dependency_license']}): {c['issue']}")
    for q in result["clarifying_questions"]:
        print(f"  ? {q}")
    for rec in result["recommendations"]:
        print(f"\n{rec['rank']}. {rec['spdx_id']} - {rec['title']}\n   {rec['reason']}")
        if rec["note"]:
            print(f"   note: {rec['note']}")
        for c in rec["claims"]:
            print(f"   {BADGE[c['status']]} {c['text']}")
            print(f"{'':20}{c['clause_id']}: \"{c['quote'][:120]}\"  ({c['reason']})")
    t = result["timings"]
    print(f"\n{result['disclaimer']}\n[{result['model']} | {t['total_s']}s | tokens {result['usage']}]")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--description", help="project description")
    parser.add_argument("--manifest", help="requirements.txt, pyproject.toml or package.json")
    parser.add_argument("--model", default=llm.PIPELINE_MODEL)
    parser.add_argument("--no-verify", action="store_true", help="skip the NLI verifier (baseline)")
    parser.add_argument("--json", help="also write the full result to this file")
    args = parser.parse_args()
    if not args.description and not args.manifest:
        parser.error("give --description, --manifest, or both")

    result = pipeline.recommend(args.description, args.manifest, model=args.model,
                                verify=not args.no_verify)
    if args.no_verify:
        for rec in result["recommendations"]:
            for c in rec["claims"]:
                c.setdefault("status", "unverified")
                c.setdefault("reason", "not checked")
    show(result)
    if args.json:
        Path(args.json).write_text(json.dumps(result, indent=2))
        print(f"wrote {args.json}")


if __name__ == "__main__":
    main()
