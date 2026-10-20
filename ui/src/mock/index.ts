// Mock data: real outputs saved from the v1 pipeline (scripts/recommend.py) and the
// in-scope license knowledge base. Replace with API calls once the backend exists.

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
  result: Result;
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

export const HISTORY = [
  { id: "clinic", when: "Oct 17, 16:42", example: EXAMPLES[1] },
  { id: "saas", when: "Oct 17, 15:58", example: EXAMPLES[0] },
];

export const PIPELINE_STEPS = [
  { title: "Input handler", detail: "Validate description and manifest", ms: 400 },
  { title: "Dependency license lookup", detail: "PyPI / npm metadata → SPDX IDs", ms: 700 },
  { title: "Stage 1 · recommend", detail: "gpt-oss-120b infers requirements, picks 3 licenses", ms: 1400 },
  { title: "Clause retrieval", detail: "Relevant clauses from the knowledge base", ms: 450 },
  { title: "Stage 2 · explain", detail: "Claims that quote a clause", ms: 1500 },
  { title: "NLI verifier", detail: "DeBERTa checks each claim against its clause", ms: 1000 },
  { title: "Response builder", detail: "Rank, label and assemble the result", ms: 350 },
];
