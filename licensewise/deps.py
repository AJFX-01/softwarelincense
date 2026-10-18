"""Read a dependency manifest and look up each dependency's declared license.

Supported manifests: requirements.txt, pyproject.toml ([project].dependencies),
package.json ("dependencies" only: devDependencies are not distributed).
Licenses come from registry metadata (PyPI JSON API, npm registry) and are
normalized to SPDX IDs. Anything that cannot be mapped is reported as unknown,
never guessed.
"""

import json
import re
import tomllib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx

from licensewise import DATA

SPDX_IDS = {i.lower(): i for i in json.loads((DATA / "spdx_ids.json").read_text())}

# Free-text names and trove classifiers seen in registry metadata -> SPDX.
ALIASES = {
    "mit": "MIT", "mit license": "MIT", "the mit license": "MIT",
    "apache 2.0": "Apache-2.0", "apache-2": "Apache-2.0", "apache 2": "Apache-2.0",
    "apache license 2.0": "Apache-2.0", "apache license, version 2.0": "Apache-2.0",
    "apache software license": "Apache-2.0",
    "bsd-3": "BSD-3-Clause", "bsd 3-clause": "BSD-3-Clause", "new bsd": "BSD-3-Clause",
    "bsd-2": "BSD-2-Clause", "bsd 2-clause": "BSD-2-Clause", "simplified bsd": "BSD-2-Clause",
    "isc license": "ISC", "isc license (iscl)": "ISC",
    "gpl v3": "GPL-3.0-only", "gplv3": "GPL-3.0-only", "gpl-3": "GPL-3.0-only", "gpl3": "GPL-3.0-only",
    "gnu general public license v3 (gplv3)": "GPL-3.0-only",
    "gnu general public license v3 or later (gplv3+)": "GPL-3.0-or-later",
    "gpl v2": "GPL-2.0-only", "gplv2": "GPL-2.0-only", "gpl-2": "GPL-2.0-only", "gpl2": "GPL-2.0-only",
    "gnu general public license v2 (gplv2)": "GPL-2.0-only",
    "gnu general public license v2 or later (gplv2+)": "GPL-2.0-or-later",
    "lgplv3": "LGPL-3.0-only", "gnu lesser general public license v3 (lgplv3)": "LGPL-3.0-only",
    "lgplv2": "LGPL-2.1-only", "gnu lesser general public license v2 (lgplv2)": "LGPL-2.1-only",
    "agplv3": "AGPL-3.0-only", "gnu affero general public license v3": "AGPL-3.0-only",
    "mozilla public license 2.0 (mpl 2.0)": "MPL-2.0", "mpl 2.0": "MPL-2.0", "mpl-2": "MPL-2.0",
    "the unlicense (unlicense)": "Unlicense", "public domain": None,  # not a license ID
    "python software foundation license": "PSF-2.0",
}
GENERIC_CLASSIFIERS = {"osi approved", "other/proprietary license", "free for non-commercial use"}


def normalize(raw):
    """Map a registry license string to SPDX ID(s) or an SPDX expression; None if unknown."""
    if not raw:
        return None
    text = raw.strip()
    if "\n" in text or len(text) > 100:  # full license text pasted into the field
        return None
    key = text.lower().removeprefix("license :: ").removeprefix("osi approved :: ").strip()
    if key in SPDX_IDS:
        return SPDX_IDS[key]
    if key in ALIASES:
        return ALIASES[key]
    # SPDX expression such as "MIT OR Apache-2.0" or "(BSD-3-Clause AND MIT)"
    tokens = re.findall(r"[A-Za-z0-9.+-]+", text)
    ids = [t for t in tokens if t.upper() not in {"AND", "OR", "WITH"}]
    if ids and all(t.lower() in SPDX_IDS for t in ids):
        return " ".join(SPDX_IDS.get(t.lower(), t.upper()) for t in tokens)
    return None


def parse_manifest(path):
    """Return (ecosystem, [package names])."""
    path = Path(path)
    name = path.name.lower()
    if name == "package.json":
        data = json.loads(path.read_text())
        return "npm", sorted(data.get("dependencies", {}))
    if name == "pyproject.toml":
        data = tomllib.loads(path.read_text())
        specs = data.get("project", {}).get("dependencies", [])
        return "pypi", sorted({_requirement_name(s) for s in specs if _requirement_name(s)})
    if name.endswith(".txt"):
        names = set()
        for line in path.read_text().splitlines():
            line = line.split("#", 1)[0].strip()
            if line and not line.startswith(("-", "git+", "http")):
                if n := _requirement_name(line):
                    names.add(n)
        return "pypi", sorted(names)
    raise ValueError(f"Unsupported manifest: {path.name} (use requirements.txt, pyproject.toml or package.json)")


def _requirement_name(spec):
    match = re.match(r"\s*([A-Za-z0-9][A-Za-z0-9._-]*)", spec)
    return match.group(1).lower() if match else None


def _lookup_pypi(client, name):
    response = client.get(f"https://pypi.org/pypi/{name}/json")
    if response.status_code != 200:
        return None, f"not found on PyPI ({response.status_code})"
    info = response.json()["info"]
    for raw in (info.get("license_expression"), info.get("license")):
        if spdx := normalize(raw):
            return spdx, raw
    for classifier in info.get("classifiers", []):
        if classifier.startswith("License ::"):
            tail = classifier.split("::")[-1].strip()
            if tail.lower() not in GENERIC_CLASSIFIERS and (spdx := normalize(classifier)):
                return spdx, classifier
    raw = info.get("license_expression") or info.get("license") or ""
    return None, raw[:80] or "no license metadata"


def _lookup_npm(client, name):
    response = client.get(f"https://registry.npmjs.org/{name}/latest")
    if response.status_code != 200:
        return None, f"not found on npm ({response.status_code})"
    raw = response.json().get("license")
    if isinstance(raw, dict):  # old format: {"type": "MIT", "url": ...}
        raw = raw.get("type")
    return normalize(raw), raw or "no license metadata"


def dependency_licenses(manifest_path):
    """[{name, ecosystem, license (SPDX or None), declared (raw metadata)}]"""
    ecosystem, names = parse_manifest(manifest_path)
    lookup = _lookup_npm if ecosystem == "npm" else _lookup_pypi
    with httpx.Client(timeout=15, follow_redirects=True) as client, ThreadPoolExecutor(8) as pool:
        results = list(pool.map(lambda n: (n, *lookup(client, n)), names))
    return [{"name": n, "ecosystem": ecosystem, "license": spdx, "declared": raw}
            for n, spdx, raw in results]
