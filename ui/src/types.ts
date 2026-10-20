// Shapes match the JSON returned by licensewise.pipeline.recommend().

export type Status = "verified" | "unverified" | "contradicted";

export interface Claim {
  text: string;
  clause_id: string;
  quote: string;
  quote_found: boolean;
  status: Status;
  reason: string;
  nli: Record<string, number> | null;
  clause_text?: string | null;
}

export interface Recommendation {
  rank: number;
  spdx_id: string;
  title: string;
  reason: string;
  claims: Claim[];
  note: string | null;
}

export interface Dependency {
  name: string;
  ecosystem: string;
  license: string | null;
  declared: string;
  in_catalogue: boolean;
}

export interface Result {
  input: { description: string | null; manifest: string | null };
  model: string;
  dependencies: Dependency[];
  requirements: { text: string; source: string }[];
  conflicts: { dependency: string; dependency_license: string; issue: string }[];
  clarifying_questions: string[];
  recommendations: Recommendation[];
  timings: Record<string, number>;
  disclaimer: string;
}

export interface License {
  spdx_id: string;
  title: string;
  nickname: string;
  description: string;
  permissions: string[];
  conditions: string[];
  limitations: string[];
  language: string;
  copyleft: "none" | "file_or_library" | "whole_work";
}

export type Page = "new" | "history" | "licenses" | "pipeline";
