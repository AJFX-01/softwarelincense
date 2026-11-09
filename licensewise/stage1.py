"""Stage 1: infer the developer's requirements and recommend the top 3 licenses."""

from typing import Literal

from pydantic import BaseModel, Field, create_model

from licensewise import kb, llm

SYSTEM = """You help software developers choose an open-source license.

You are given the developer's project description and/or the licenses of the \
project's dependencies, plus a catalogue of the licenses you may recommend.

1. List the requirements the developer actually expressed (or that the dependency \
licenses impose). Do not invent requirements the input does not support.
2. Recommend exactly 3 different licenses from the catalogue, best fit first, each with \
a one-sentence reason tied to the requirements.
3. If a dependency's license constrains what the project can be licensed under (for \
example, a strong copyleft dependency), list it as a conflict or constraint, and make \
sure your recommendations respect it.
4. If the input is too vague to choose well, add up to 2 short clarifying questions. \
Questions are in addition to the 3 recommendations, never instead of them.

Never recommend a license that is not in the catalogue."""

# Phase 2 (prompt v2): the catalogue carries each license's labels, and the model
# must check every pick against every requirement before answering. Phase 1 error
# analysis showed most wrong picks broke a stated constraint (trademark 54%,
# document-changes 39% of picks) that the labels answer directly.
SYSTEM_V2 = SYSTEM + """

Each catalogue entry lists the license's labels (permissions, conditions, \
limitations). Use them, not memory, to check fit. For example, a requirement that \
the license must not grant trademark rights needs "trademark-use" under limitations; \
a requirement that modifiers need not document their changes rules out any license \
with "document-changes" under conditions; "network-use-disclose" means users over a \
network must get the source.

Work in this order: first list the requirements, then keep only licenses whose labels \
satisfy ALL of them, then rank those. A license that breaks a stated requirement must \
not be recommended while a license that satisfies all of them exists."""

PROMPTS = {"v1": SYSTEM, "v2": SYSTEM_V2}
DEFAULT_PROMPT = "v2"


class Requirement(BaseModel):
    text: str
    source: Literal["description", "dependencies"]


class Conflict(BaseModel):
    dependency: str
    dependency_license: str
    issue: str


def _output_model():
    license_id = Literal[tuple(sorted(kb.licenses()))]
    recommendation = create_model("Recommendation", spdx_id=(license_id, ...), reason=(str, ...))
    return create_model(
        "Stage1Output",
        requirements=(list[Requirement], ...),
        recommendations=(list[recommendation], Field(min_length=3, max_length=3)),
        conflicts=(list[Conflict], ...),
        clarifying_questions=(list[str], ...),
    )


def prompt(description, dependencies, variant=DEFAULT_PROMPT):
    parts = []
    if description:
        parts.append(f"Project description:\n{description.strip()}")
    if dependencies:
        lines = [f"- {d['name']} ({d['ecosystem']}): {d['license'] or 'UNKNOWN (' + d['declared'] + ')'}"
                 for d in dependencies]
        parts.append("Dependencies and their declared licenses:\n" + "\n".join(lines))
    parts.append(f"License catalogue (recommend only from these IDs):\n{kb.catalogue(labels=variant != 'v1')}")
    return "\n\n".join(parts)


def recommend(description=None, dependencies=None, model=llm.PIPELINE_MODEL, variant=DEFAULT_PROMPT):
    if not description and not dependencies:
        raise ValueError("Provide a project description, a manifest, or both.")
    user = prompt(description, dependencies, variant)
    for _attempt in range(2):
        result = llm.complete_json(model, PROMPTS[variant], user, _output_model())
        seen, recommendations = set(), []
        for r in result.recommendations:  # drop duplicates, keep order
            if r.spdx_id not in seen:
                seen.add(r.spdx_id)
                recommendations.append({"spdx_id": r.spdx_id, "reason": r.reason})
        if len(recommendations) == 3:
            break
        # The schema cannot require distinct IDs, so ask again once.
        user += ("\n\nYour previous answer repeated a license. Recommend 3 DIFFERENT "
                 "license IDs; the 2nd and 3rd may be weaker fits.")
    return {
        "requirements": [r.model_dump() for r in result.requirements],
        "recommendations": recommendations[:3],
        "conflicts": [c.model_dump() for c in result.conflicts],
        "clarifying_questions": result.clarifying_questions[:2],
    }
