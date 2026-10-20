import type { License } from "./types";

export const ALLOWED_MANIFESTS = ["requirements.txt", "pyproject.toml", "package.json"];
export const MAX_MANIFEST_BYTES = 100_000;

/** Same rules as licensewise/deps.py, so the UI can preview what will be looked up. */
export function parseManifest(name: string, content: string): string[] {
  if (name === "package.json") {
    const data = JSON.parse(content);
    return Object.keys(data.dependencies ?? {}).sort();
  }
  if (name === "pyproject.toml") {
    const block = content.match(/dependencies\s*=\s*\[([\s\S]*?)\]/);
    return block ? [...block[1].matchAll(/"([A-Za-z0-9][A-Za-z0-9._-]*)/g)].map((m) => m[1].toLowerCase()) : [];
  }
  return content
    .split("\n")
    .map((l) => l.split("#")[0].trim())
    .filter((l) => l && !/^(-|git\+|http)/.test(l))
    .map((l) => (l.match(/^[A-Za-z0-9][A-Za-z0-9._-]*/)?.[0] ?? "").toLowerCase())
    .filter(Boolean);
}

export function validateManifest(file: File): string | null {
  if (!ALLOWED_MANIFESTS.includes(file.name)) {
    return `Unsupported file "${file.name}". Upload requirements.txt, pyproject.toml or package.json.`;
  }
  if (file.size > MAX_MANIFEST_BYTES) return "File is larger than 100 KB.";
  return null;
}

export const COPYLEFT_LABEL: Record<License["copyleft"], string> = {
  none: "Permissive",
  file_or_library: "Weak copyleft",
  whole_work: "Strong copyleft",
};

export function humanize(label: string): string {
  return label.replace(/--/g, " · ").replace(/-/g, " ");
}

/** Split clause text around the quote (case- and whitespace-insensitive) for highlighting. */
export function highlight(clause: string, quote: string): [string, string, string] {
  const norm = (s: string) => s.toLowerCase().replace(/\s+/g, " ");
  const c = norm(clause);
  const q = norm(quote).trim().replace(/^["'.]+|["'.]+$/g, "");
  const i = q ? c.indexOf(q) : -1;
  if (i < 0) return [clause, "", ""];
  // clause may contain runs of whitespace; map normalized index back conservatively
  const flat = clause.replace(/\s+/g, " ");
  return [flat.slice(0, i), flat.slice(i, i + q.length), flat.slice(i + q.length)];
}
