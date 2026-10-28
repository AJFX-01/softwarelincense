"""In-scope license knowledge base (choosealicense.com labels + full texts)."""

import json
from functools import cache

from licensewise import DATA


@cache
def licenses():
    """SPDX ID -> license record, for in-scope licenses (software + OSI-approved)."""
    records = json.loads((DATA / "licenses.json").read_text())
    return {l["spdx_id"]: l for l in records if l["in_scope"]}


def kb_id(spdx_id):
    """Map an SPDX ID to the knowledge base's ID: GPL-3.0-only / GPL-3.0-or-later -> GPL-3.0."""
    if not spdx_id:
        return None
    for suffix in ("-only", "-or-later", "+"):
        if spdx_id.endswith(suffix):
            spdx_id = spdx_id[: -len(suffix)]
    return spdx_id if spdx_id in licenses() else None


def catalogue():
    """One line per in-scope license, for the Stage 1 prompt."""
    return "\n".join(f"- {i}: {l['title']}. {l['description']}" for i, l in sorted(licenses().items()))


def copyleft(lic):
    """"none", "file_or_library" or "whole_work" from the labels (same rule as scripts/build_scenarios.py)."""
    conditions = set(lic["conditions"])
    if "same-license" in conditions:
        return "whole_work"
    if conditions & {"same-license--file", "same-license--library"}:
        return "file_or_library"
    return "none"
