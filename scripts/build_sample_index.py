"""Join the 20k license-blob sample with the dataset's metadata CSVs.

Inputs (project root):
    sample20k/<xx>/<yy>/<sha1>   license files from blobs-sample20k.tar.zst
    license-blobs.csv            sha1 <-> swhid, filenames
    blobs-fileinfo.csv           mime type, encoding, size (keyed by sha1)
    blobs-scancode.csv           detected SPDX licenses + score (keyed by sha1)
    blobs-earliest.csv           first commit, occurrences (keyed by swhid)
    blobs-origins.csv            example origin URL (keyed by swhid)
    data/processed/licenses.json from build_license_kb.py

Output:
    data/processed/sample20k_index.csv, one row per sample blob.

The big CSVs are streamed and filtered to the sample, so memory stays small.
"""

import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SAMPLE_DIR = ROOT / "sample20k"
KB = ROOT / "data" / "processed" / "licenses.json"
OUT = ROOT / "data" / "processed" / "sample20k_index.csv"

csv.field_size_limit(sys.maxsize)


def normalize(spdx_id):
    """Map ScanCode IDs (GPL-3.0-only, GPL-2.0-or-later) to choosealicense IDs (GPL-3.0)."""
    for suffix in ("-only", "-or-later", "+"):
        if spdx_id.endswith(suffix):
            return spdx_id[: -len(suffix)]
    return spdx_id


def stream(name, delimiter=",", header=True):
    with open(ROOT / name, newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f, delimiter=delimiter)
        if header:
            next(reader)
        yield from reader


def categorize(row, in_scope_ids):
    detected = row["licenses"]
    if not detected:
        return "undetected"
    normalized = {normalize(l) for l in detected}
    if not normalized & in_scope_ids:
        return "out_of_scope"
    if len(set(detected)) > 1:
        return "multi"
    if row["max_score"] < 100:
        return "variant"
    return "clean"


def main():
    in_scope_ids = {l["spdx_id"] for l in json.loads(KB.read_text()) if l["in_scope"]}

    rows = {p.name: {"sha1": p.name, "path": str(p.relative_to(ROOT))}
            for p in SAMPLE_DIR.glob("*/*/*") if p.is_file()}
    print(f"sample blobs: {len(rows)}")

    names = defaultdict(set)
    swhid_to_sha1 = {}
    for swhid, sha1, name in stream("license-blobs.csv"):
        if sha1 in rows:
            names[sha1].add(name)
            swhid_to_sha1[swhid] = sha1
    for swhid, sha1 in swhid_to_sha1.items():
        rows[sha1]["swhid"] = swhid
    print("joined license-blobs")

    for sha1, mime, enc, lines, words, size in stream("blobs-fileinfo.csv"):
        if sha1 in rows:
            rows[sha1].update(mime_type=mime, encoding=enc, line_count=lines,
                              word_count=words, size=size)
    print("joined fileinfo")

    detections = defaultdict(list)
    for sha1, license_id, score in stream("blobs-scancode.csv"):
        if sha1 in rows:
            detections[sha1].append((license_id, float(score)))
    print("joined scancode")

    for swhid, _rev, ts, occurrences in stream("blobs-earliest.csv", delimiter="\t"):
        sha1 = swhid_to_sha1.get(swhid)
        if sha1:
            rows[sha1].update(earliest_ts=ts, occurrences=occurrences)
    print("joined earliest")

    for swhid, url in stream("blobs-origins.csv", delimiter="\t", header=False):
        sha1 = swhid_to_sha1.get(swhid)
        if sha1:
            rows[sha1]["origin_url"] = url
    print("joined origins")

    for sha1, row in rows.items():
        found = sorted(detections[sha1], key=lambda d: -d[1])
        row["licenses"] = [l for l, _ in found]
        row["max_score"] = found[0][1] if found else 0.0
        row["category"] = categorize(row, in_scope_ids)
        row["in_scope_license"] = next(
            (normalize(l) for l in row["licenses"] if normalize(l) in in_scope_ids), "")
        row["filenames"] = ";".join(sorted(names[sha1]))
        row["licenses"] = ";".join(row["licenses"])

    columns = ["sha1", "swhid", "path", "filenames", "mime_type", "encoding",
               "line_count", "word_count", "size", "licenses", "max_score",
               "in_scope_license", "category", "occurrences", "earliest_ts", "origin_url"]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(sorted(rows.values(), key=lambda r: r["sha1"]))
    print(f"wrote {OUT.relative_to(ROOT)}\n")

    print("category counts:")
    for category, n in Counter(r["category"] for r in rows.values()).most_common():
        print(f"  {category:13} {n:6}")
    print("\ntop in-scope licenses (clean + variant + multi):")
    in_scope = Counter(r["in_scope_license"] for r in rows.values() if r["in_scope_license"])
    for license_id, n in in_scope.most_common(15):
        print(f"  {license_id:16} {n:6}")


if __name__ == "__main__":
    main()
