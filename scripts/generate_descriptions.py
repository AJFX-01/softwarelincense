"""Turn requirement profiles into natural-language project descriptions (Groq).

For each profile in data/processed/scenarios/profiles.jsonl:
  1. Generate: DESCRIPTION_MODEL (Qwen) writes several first-person project
     descriptions, each from a different persona, that imply exactly the
     profile's requirements.
  2. Validate (round trip): CHECK_MODEL (gpt-oss-20b, a different model family)
     reads each description cold and recovers the requirements. A description
     is kept only if the recovered requirements match the profile exactly.

The pipeline itself runs on gpt-oss-120b, so the test descriptions are not
written by the model being evaluated.

Output: data/processed/scenarios/descriptions.jsonl (appended; already-processed
profiles are skipped, so the script can be re-run after an interruption).

Usage:
    .venv/bin/python scripts/generate_descriptions.py --dry-run     # print prompts, no API calls
    .venv/bin/python scripts/generate_descriptions.py --limit 3     # small trial
    .venv/bin/python scripts/generate_descriptions.py               # all profiles
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import groq  # noqa: E402

from build_scenarios import DIMENSIONS  # noqa: E402
from licensewise import llm  # noqa: E402

PROFILES = ROOT / "data" / "processed" / "scenarios" / "profiles.jsonl"
OUT = ROOT / "data" / "processed" / "scenarios" / "descriptions.jsonl"


class Description(BaseModel):
    persona: str
    text: str


class Descriptions(BaseModel):
    descriptions: list[Description]


class Recovered(BaseModel):
    share_changes: Literal["none", "file_or_library", "whole_work", "unspecified"]
    network_use: Literal["must_disclose", "must_not_trigger", "unspecified"]
    patent_grant: Literal["required", "unspecified"]
    trademark: Literal["protected", "unspecified"]
    attribution: Literal["not_required", "unspecified"]
    document_changes: Literal["not_required", "unspecified"]


GENERATE_SYSTEM = """You write realistic project descriptions that software developers \
would type into a tool that recommends an open-source license.

Rules:
- Write in the first person, as the developer, in 2-4 sentences.
- Mention what the project is, then express every listed requirement in your own words, \
the way a real developer would (plain language, not legal terms).
- Express ONLY the listed requirements. Do not state or imply preferences on anything else.
- Never name a specific license (MIT, GPL, Apache, ...) or an SPDX identifier.
- Each description must use a different persona and project type \
(e.g. student, startup founder, hobbyist, researcher, company engineer)."""

VALIDATE_SYSTEM = """You read a developer's project description and identify what they \
need from an open-source license. For each dimension, choose the value whose meaning the \
description clearly expresses, or "unspecified" if the description does not address it. \
Do not guess from the type of project; only use what the developer actually says."""


def dimension_guide():
    lines = []
    for dim, values in DIMENSIONS.items():
        lines.append(f"{dim}:")
        for value, (meaning, _) in values.items():
            lines.append(f'  - "{value}": {meaning}')
        lines.append('  - "unspecified": the description does not address this.')
    return "\n".join(lines)


def generate_prompt(profile, n):
    requirements = "\n".join(f"- {r}" for r in profile["requirements"])
    return (f"Write {n} project descriptions. Each must express exactly these "
            f"requirements:\n{requirements}")


def validate_prompt(text):
    return f"Dimensions:\n{dimension_guide()}\n\nDescription:\n{text}"


def matches(profile, recovered):
    expected = {dim: profile["constraints"].get(dim, "unspecified") for dim in DIMENSIONS}
    got = recovered.model_dump()
    return expected == got, got


def done_profiles():
    if not OUT.exists():
        return set()
    return {json.loads(line)["profile_id"] for line in OUT.read_text().splitlines() if line}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-profile", type=int, default=3, help="descriptions per profile")
    parser.add_argument("--limit", type=int, help="process at most this many new profiles")
    parser.add_argument("--dry-run", action="store_true", help="print prompts, make no API calls")
    args = parser.parse_args()

    profiles = [json.loads(line) for line in PROFILES.read_text().splitlines() if line]
    skip = done_profiles()
    todo = [p for p in profiles if p["profile_id"] not in skip][: args.limit]
    print(f"{len(profiles)} profiles, {len(skip)} already done, {len(todo)} to process")
    print(f"generator: {llm.DESCRIPTION_MODEL} | checker: {llm.CHECK_MODEL}")

    if args.dry_run:
        p = todo[0]
        print(f"\n--- generate system ---\n{GENERATE_SYSTEM}")
        print(f"\n--- generate prompt ({p['profile_id']}) ---\n{generate_prompt(p, args.per_profile)}")
        print(f"\n--- validate system ---\n{VALIDATE_SYSTEM}")
        print(f"\n--- validate prompt ---\n{validate_prompt('<description text>')}")
        return

    kept = total = 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    for i, profile in enumerate(todo, 1):
        try:
            # Qwen's free tier rejects requests whose max_tokens exceeds 1,000 output tokens/minute.
            generated = llm.complete_json(llm.DESCRIPTION_MODEL, GENERATE_SYSTEM,
                                          generate_prompt(profile, args.per_profile), Descriptions,
                                          max_tokens=1000)
            rows = []
            for d in generated.descriptions:
                recovered = llm.complete_json(llm.CHECK_MODEL, VALIDATE_SYSTEM,
                                              validate_prompt(d.text), Recovered)
                valid, got = matches(profile, recovered)
                rows.append({"profile_id": profile["profile_id"], "persona": d.persona,
                             "text": d.text, "recovered": got, "valid": valid,
                             "gold": profile["gold"], "generator": llm.DESCRIPTION_MODEL,
                             "checker": llm.CHECK_MODEL})
        except groq.AuthenticationError:
            raise SystemExit("Groq rejected the API key in .env.")
        except (groq.APIStatusError, groq.APIConnectionError, ValueError) as e:
            print(f"  {profile['profile_id']}: skipped ({str(e)[:200]})")
            continue

        # Write a profile's rows together so a re-run never leaves it half done.
        with open(OUT, "a", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row) + "\n")
        kept += sum(r["valid"] for r in rows)
        total += len(rows)
        print(f"[{i}/{len(todo)}] {profile['profile_id']}: "
              f"{sum(r['valid'] for r in rows)}/{len(rows)} passed round trip", flush=True)

    print(f"\nkept {kept}/{total} descriptions -> {OUT.relative_to(ROOT)}")
    print("tokens:", dict(llm.USAGE))


if __name__ == "__main__":
    main()
