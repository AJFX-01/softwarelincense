"""Stage 2: explain a recommended license with claims that quote its clauses.

Only the clauses relevant to the license's labelled obligations are sent (found
with licensewise.clauses), not the full text: the full GPL-3.0 text alone is
larger than Groq's free-tier limit of 8,000 tokens per minute.
"""

from pydantic import BaseModel

from licensewise import kb, llm
from licensewise.clauses import LABEL_PATTERNS, best_clause, clauses

MAX_EVIDENCE_CHARS = 12000

SYSTEM = """You explain an open-source license to a software developer in plain language.

You are given numbered clauses from the license and the developer's requirements. \
Write 3 to 5 short claims about what the license means for this developer, most \
relevant first.

Rules for every claim:
- It must be fully supported by ONE of the numbered clauses. Cite that clause's ID.
- Include a quote copied EXACTLY, character for character, from that clause (at most \
300 characters) that supports the claim.
- State only what the quoted clause says. Do not add information from outside the clauses.
- Plain language, one sentence."""


class Claim(BaseModel):
    text: str
    clause_id: str
    quote: str


class Explanation(BaseModel):
    claims: list[Claim]


def evidence(spdx_id):
    """{clause_id: clause text} for the clauses that express the license's labels."""
    lic = kb.licenses()[spdx_id]
    paras = clauses(lic["text"])
    picked = []
    for (category, label) in LABEL_PATTERNS:
        if label in lic[category]:
            clause = best_clause(paras, (category, label))
            if clause and clause not in picked:
                picked.append(clause)
    ordered = [p for p in paras if p in picked]  # keep the license's own order
    selected, total = {}, 0
    for i, clause in enumerate(ordered, 1):
        if total + len(clause) > MAX_EVIDENCE_CHARS:
            break
        selected[f"C{i}"] = clause
        total += len(clause)
    return selected


def prompt(spdx_id, clauses_by_id, requirements, feedback=None):
    lic = kb.licenses()[spdx_id]
    reqs = "\n".join(f"- {r['text']}" for r in requirements) or "- (none stated)"
    numbered = "\n\n".join(f"[{cid}] {text}" for cid, text in clauses_by_id.items())
    text = (f"License: {lic['title']} ({spdx_id})\n\nDeveloper requirements:\n{reqs}\n\n"
            f"Clauses:\n{numbered}")
    if feedback:
        text += ("\n\nYour previous claims below could not be verified against their cited "
                 "clause. Rewrite them so each one says only what its quote says, using the "
                 "clause's own wording where possible:\n" + "\n".join(f"- {f}" for f in feedback))
    return text


def explain(spdx_id, requirements, model=llm.PIPELINE_MODEL, feedback=None):
    clauses_by_id = evidence(spdx_id)
    result = llm.complete_json(model, SYSTEM, prompt(spdx_id, clauses_by_id, requirements, feedback),
                               Explanation)
    return clauses_by_id, [c.model_dump() for c in result.claims]
