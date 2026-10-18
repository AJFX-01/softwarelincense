"""Build requirement profiles and their gold license sets.

A profile is a set of constraints a developer might have (e.g. "changes must be
shared", "patent grant required"). Each constraint is a rule over the
choosealicense.com labels, so the gold set for a profile -- every in-scope
license that satisfies all of its constraints -- is computed deterministically.
No human judgment is involved.

Output: data/processed/scenarios/profiles.jsonl, one profile per line.
"""

import itertools
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KB = ROOT / "data" / "processed" / "licenses.json"
OUT = ROOT / "data" / "processed" / "scenarios" / "profiles.jsonl"

SAME_LICENSE_WEAK = {"same-license--file", "same-license--library"}


def copyleft(lic):
    conditions = set(lic["conditions"])
    if "same-license" in conditions:
        return "whole_work"
    if conditions & SAME_LICENSE_WEAK:
        return "file_or_library"
    return "none"


# dimension -> value -> (plain-English meaning, predicate over a license).
# A dimension left out of a profile means "don't care".
DIMENSIONS = {
    "share_changes": {
        "none": ("Others may keep their changes private and use any license for derived work.",
                 lambda l: copyleft(l) == "none"),
        "file_or_library": ("Changes to the project's own files or library must stay open, "
                            "but it can be combined with closed-source code.",
                            lambda l: copyleft(l) == "file_or_library"),
        "whole_work": ("Any derived work that is distributed must be released under the same license.",
                       lambda l: copyleft(l) == "whole_work"),
    },
    "network_use": {
        "must_disclose": ("Offering the software to users over a network (e.g. SaaS) must "
                          "trigger the obligation to share source code.",
                          lambda l: "network-use-disclose" in l["conditions"]),
        "must_not_trigger": ("Running the software as a network service must NOT by itself "
                             "require sharing source code.",
                             lambda l: "network-use-disclose" not in l["conditions"]),
    },
    "patent_grant": {
        "required": ("Contributors must explicitly grant users rights to their patents.",
                     lambda l: "patent-use" in l["permissions"]),
    },
    "trademark": {
        "protected": ("The license must explicitly NOT grant rights to the project's "
                      "name, logos, or trademarks.",
                      lambda l: "trademark-use" in l["limitations"]),
    },
    "attribution": {
        "not_required": ("Users should not even have to keep a copyright notice; "
                         "the code should be as close to public domain as possible.",
                         lambda l: not any(c.startswith("include-copyright") for c in l["conditions"])),
    },
    "document_changes": {
        "not_required": ("People who modify the code should not be obliged to document "
                         "or mark what they changed.",
                         lambda l: "document-changes" not in l["conditions"]),
    },
}


def main():
    licenses = [l for l in json.loads(KB.read_text()) if l["in_scope"]]
    all_ids = sorted(l["spdx_id"] for l in licenses)

    options = [[None, *values] for values in DIMENSIONS.values()]
    profiles, seen_gold = [], Counter()
    for combo in itertools.product(*options):
        constraints = {dim: value for dim, value in zip(DIMENSIONS, combo) if value}
        if not constraints:
            continue
        gold = sorted(
            l["spdx_id"] for l in licenses
            if all(DIMENSIONS[d][v][1](l) for d, v in constraints.items())
        )
        if not gold:
            continue
        seen_gold[tuple(gold)] += 1
        profiles.append({
            "profile_id": f"P{len(profiles) + 1:03d}",
            "constraints": constraints,
            "requirements": [DIMENSIONS[d][v][0] for d, v in constraints.items()],
            "gold": gold,
            "gold_size": len(gold),
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        for p in profiles:
            f.write(json.dumps(p) + "\n")

    sizes = [p["gold_size"] for p in profiles]
    print(f"{len(all_ids)} in-scope licenses")
    print(f"{len(profiles)} profiles with a non-empty gold set -> {OUT.relative_to(ROOT)}")
    print(f"  distinct gold sets: {len(seen_gold)}")
    print(f"  gold size: min {min(sizes)}, median {sorted(sizes)[len(sizes) // 2]}, max {max(sizes)}")
    print(f"  profiles with a single correct answer: {sum(s == 1 for s in sizes)}")
    print("\ncopyleft class per license:")
    for cls in ("none", "file_or_library", "whole_work"):
        print(f"  {cls:16} {', '.join(l['spdx_id'] for l in licenses if copyleft(l) == cls)}")


if __name__ == "__main__":
    main()
