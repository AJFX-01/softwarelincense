// Saved outputs of the v1 pipeline (scripts/recommend.py) and the in-scope license
// knowledge base. Used for the demo links (?example=...) and when the backend is offline.

import type { License, Result } from "../types";
import saas from "./demo_saas.json";
import clinic from "./demo_manifest.json";
import licenses from "./licenses.json";

export const LICENSES = licenses as License[];

export const SAMPLE_REQUIREMENTS = `requests>=2.31
numpy==2.1.0  # arrays
django
pyqt5
black[jupyter]
this-package-does-not-exist-xyz
`;

export interface Example {
  id: string;
  label: string;
  description: string;
  manifest: { name: string; content: string } | null;
  result: Result | null; // null while a backend run is still in progress
  jobId?: string; // set when opened from History (a real run)
}

export const EXAMPLES: Example[] = [
  {
    id: "saas",
    label: "SaaS analytics library",
    description: (saas as Result).input.description ?? "",
    manifest: null,
    result: saas as Result,
  },
  {
    id: "clinic",
    label: "Clinic app + requirements.txt",
    description: (clinic as Result).input.description ?? "",
    manifest: { name: "requirements.txt", content: SAMPLE_REQUIREMENTS },
    result: clinic as Result,
  },
];

// Same keys and order as STEPS in licensewise/api.py.
export const PIPELINE_STEPS = [
  { key: "input", title: "Input handler", detail: "Validate description and manifest" },
  { key: "dependencies", title: "Dependency license lookup", detail: "PyPI / npm metadata → SPDX IDs" },
  { key: "stage1", title: "Stage 1 · recommend", detail: "gpt-oss-120b infers requirements, picks 3 licenses" },
  { key: "retrieval", title: "Clause retrieval", detail: "Relevant clauses from the knowledge base" },
  { key: "explain", title: "Stage 2 · explain", detail: "Claims that quote a clause" },
  { key: "verify", title: "NLI verifier", detail: "DeBERTa checks each claim against its clause" },
  { key: "response", title: "Response builder", detail: "Rank, label and assemble the result" },
];
