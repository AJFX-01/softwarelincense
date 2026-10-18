"""Build the license knowledge base from choosealicense.com.

Each file in choosealicense.com/_licenses/ has YAML front matter (SPDX ID,
permissions, conditions, limitations) followed by the full license text.
These are the v1 pipeline's canonical texts and the evaluation ground truth.

Usage:
    git clone --depth 1 https://github.com/github/choosealicense.com.git data/external/choosealicense
    python3 scripts/build_license_kb.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from licensewise.clauses import text_language  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "external" / "choosealicense" / "_licenses"
SPDX = ROOT / "data" / "external" / "spdx-licenses.json"
OUT = ROOT / "data" / "processed" / "licenses.json"
SPDX_IDS = ROOT / "data" / "processed" / "spdx_ids.json"

LIST_FIELDS = ("permissions", "conditions", "limitations")
SCALAR_FIELDS = ("title", "spdx-id", "nickname", "description", "hidden")

# Licenses on choosealicense.com that are not meant for software.
NON_SOFTWARE = {
    "CC-BY-4.0": "media",
    "CC-BY-SA-4.0": "media",
    "GFDL-1.3": "documentation",
    "ODbL-1.0": "data",
    "OFL-1.1": "fonts",
    "CERN-OHL-P-2.0": "hardware",
    "CERN-OHL-S-2.0": "hardware",
    "CERN-OHL-W-2.0": "hardware",
}


def osi_flags():
    """SPDX ID -> isOsiApproved. choosealicense uses older IDs (GPL-3.0), so also map -only."""
    flags = {}
    for entry in json.loads(SPDX.read_text())["licenses"]:
        flags[entry["licenseId"]] = entry.get("isOsiApproved", False)
    return flags


def is_osi_approved(spdx_id, flags):
    return flags.get(spdx_id) or flags.get(f"{spdx_id}-only", False)


def parse(path):
    raw = path.read_text(encoding="utf-8")
    _, front, text = raw.split("---\n", 2)

    meta = {f: [] for f in LIST_FIELDS}
    current = None
    for line in front.splitlines():
        if not line.strip():
            continue
        if line.startswith("  - ") and current in LIST_FIELDS:
            meta[current].append(line[4:].strip())
        elif not line.startswith(" "):
            key, _, value = line.partition(":")
            current = key.strip()
            if current in SCALAR_FIELDS:
                meta[current] = value.strip()

    return {
        "spdx_id": meta["spdx-id"],
        "key": path.stem,
        "title": meta.get("title", ""),
        "nickname": meta.get("nickname", ""),
        "description": meta.get("description", ""),
        "hidden": meta.get("hidden", "true") == "true",
        "permissions": meta["permissions"],
        "conditions": meta["conditions"],
        "limitations": meta["limitations"],
        "text": text.strip() + "\n",
    }


def main():
    flags = osi_flags()
    licenses = sorted((parse(p) for p in SRC.glob("*.txt")), key=lambda l: l["spdx_id"])
    for lic in licenses:
        lic["intended_for"] = NON_SOFTWARE.get(lic["spdx_id"], "software")
        lic["osi_approved"] = bool(is_osi_approved(lic["spdx_id"], flags))
        lic["in_scope"] = lic["intended_for"] == "software" and lic["osi_approved"]
        lic["language"] = text_language(lic["text"])  # NLI verifier is English-only

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(licenses, indent=2), encoding="utf-8")
    # All SPDX IDs, so dependency licenses can be normalized without data/external/.
    SPDX_IDS.write_text(json.dumps(sorted(flags)), encoding="utf-8")

    in_scope = [l["spdx_id"] for l in licenses if l["in_scope"]]
    print(f"{len(licenses)} licenses -> {OUT.relative_to(ROOT)}")
    print(f"  in scope (software + OSI-approved): {len(in_scope)}")
    for lic in licenses:
        if not lic["in_scope"]:
            reason = lic["intended_for"] if lic["intended_for"] != "software" else "not OSI-approved"
            print(f"  excluded {lic['spdx_id']:16} ({reason})")
    for lic in licenses:
        if lic["in_scope"] and lic["language"] != "en":
            print(f"  note: {lic['spdx_id']} text is '{lic['language']}'; its claims cannot be NLI-verified")
    for field in LIST_FIELDS:
        labels = sorted({label for l in licenses for label in l[field]})
        print(f"  {field} ({len(labels)}): {', '.join(labels)}")


if __name__ == "__main__":
    main()
