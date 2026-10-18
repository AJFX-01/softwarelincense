"""Split license texts into clauses and find the clause that expresses a label.

Used by the NLI test-set builder and by Stage 2 of the pipeline, which only
sends the relevant clauses of a license to the LLM (the full text of a long
license such as GPL-3.0 does not fit in one request on Groq's free tier).
"""

import re

MIN_CLAUSE_CHARS = 80
MAX_LEAD_CHARS = 1200

FRENCH_WORDS = {"le", "la", "les", "des", "du", "de", "est", "et", "en", "une", "un", "dans",
                "pour", "sur", "au", "aux", "par", "qui", "que", "ne", "pas", "ou", "son",
                "ses", "sont", "à"}
LIST_ITEM = re.compile(r"^\(?([a-z]|\d{1,2}|[ivx]{1,4})[).]\s", re.IGNORECASE)

# (category, label) -> (anchor, keywords). The anchor is a high-precision phrase
# that marks the operative clause; the broader keyword pattern is the fallback.
LABEL_PATTERNS = {
    ("permissions", "commercial-use"): (
        r"\bsell\b|charge any price|for a fee",
        r"\bsell\b|commercial|charge a fee|for a fee|fee for"),
    ("permissions", "modifications"): (
        r"permission is hereby granted|grant of copyright license|conveying modified|"
        r"you may (modify|convey a work based on)|redistribution and use in source and binary forms",
        r"modif|derivative works?|adapt"),
    ("permissions", "distribution"): (
        r"permission is hereby granted|grant of copyright license|conveying verbatim copies|"
        r"redistribution and use in source and binary forms|you may (reproduce|distribute|convey)",
        r"redistribut|distribut|convey|sublicense"),
    ("permissions", "patent-use"): (
        r"grant of patent license|grants? you a .{0,80}patent license|patent license to make|"
        r"under patent claims",
        r"patent (license|rights?)|license under .*patent|grants? .*patent"),
    ("conditions", "include-copyright"): (
        r"copyright notice .{0,120}(shall be included|must|retain)|retain the above copyright|"
        r"must retain|keep intact all notices|retain, in the source form",
        r"copyright notice|above copyright|retain .*notices?|attribution notices?"),
    ("conditions", "include-copyright--source"): (
        r"copyright notice .{0,120}(shall be included|must|retain)|must retain|retain the above copyright",
        r"copyright notice|above copyright|retain .*notices?"),
    ("conditions", "document-changes"): (
        r"prominent notices? stating|stating that you changed|you changed the files",
        r"prominent notices?|stating that you changed|you changed the files|modified files|"
        r"must be plainly marked|state the changes|notice of the modification"),
    ("conditions", "disclose-source"): (
        r"conveying non-source forms|distribution of source form|minimal corresponding source|"
        r"(must|shall) .{0,80}(source code|corresponding source)",
        r"(corresponding )?source code|source form|corresponding source"),
    ("conditions", "network-use-disclose"): (
        r"remote network interaction|over a computer network|through a computer network",
        r"network|remote(ly)?|interact"),
    ("conditions", "same-license"): (
        r"license the entire work, as a whole, under this license|"
        r"(must|shall) be (licensed|distributed|made available) under (the terms of )?this license",
        r"same license|under the terms of this license|under this license|"
        r"licensed .* under the (same|terms)|this license .* (apply|applies)"),
    ("conditions", "same-license--file"): (
        r"distribution of source form|(must|shall) be .{0,60}under the terms of this license",
        r"(covered|modified|source code) (form|files?)|file.* this license|under the terms of this license"),
    ("conditions", "same-license--library"): (
        r"conveying modified versions|modified (version|copy) .{0,80}library",
        r"library|under the terms of this license"),
    ("limitations", "liability"): (
        r"in no event|(shall|will) .{0,40}be liable|not be liable|liable to you",
        r"liab"),
    ("limitations", "warranty"): (
        r"disclaimer of warranty|without warranty|no warranty|\bas is\b",
        r"warrant"),
    ("limitations", "trademark-use"): (
        r"(does not|not) grant .{0,60}trademark",
        r"trademark|trade names?|service marks?"),
    ("limitations", "patent-use"): (
        r"(no|not) .{0,60}patent|patent.{0,60}(not|no) .{0,20}grant",
        r"patent"),
}


def is_french(paragraph):
    words = re.findall(r"[a-zàâçéèêëîïôûùüÿ]+", paragraph.lower())
    return len(words) >= 5 and sum(w in FRENCH_WORDS for w in words) / len(words) > 0.15


def text_language(text):
    paragraphs = [p for p in re.split(r"\n\s*\n", text) if p.strip()]
    french = sum(is_french(p) for p in paragraphs)
    return "fr" if french > len(paragraphs) / 2 else "en"


def clauses(text):
    """Split a license into clauses.

    - French paragraphs are skipped (the NLI models are English-only).
    - Short paragraphs (headings) are merged into the next one.
    - A paragraph ending in ':' is a lead-in: each list item that follows becomes
      its own clause with the lead-in prepended, so no clause stops at a colon.
    """
    paragraphs = [" ".join(p.split()) for p in re.split(r"\n\s*\n", text) if p.strip()]
    paragraphs = [p for p in paragraphs if not is_french(p)]

    merged, carry = [], ""
    for p in paragraphs:
        p = f"{carry} {p}".strip() if carry else p
        if len(p) < MIN_CLAUSE_CHARS and not p.endswith(":"):
            carry = p
        else:
            merged.append(p)
            carry = ""
    if carry:
        merged.append(carry)

    result, i = [], 0
    while i < len(merged):
        p = merged[i]
        if not p.endswith(":"):
            result.append(p)
            i += 1
            continue
        lead = p[:MAX_LEAD_CHARS]
        j = i + 1
        while j < len(merged) and LIST_ITEM.match(merged[j]):
            result.append(f"{lead} {merged[j]}")
            j += 1
        if j == i + 1:  # no list items: join the lead-in with the next paragraph,
            # unless that paragraph is itself a lead-in with its own list.
            if j < len(merged) and not merged[j].endswith(":"):
                result.append(f"{lead} {merged[j]}")
                j += 1
            else:
                result.append(lead)
        i = j
    return result


def best_clause(paras, key):
    """Clause that best expresses a label, or None.

    Ranked by anchor matches, then keyword matches (this separates list items
    that share a lead-in), then position (earliest wins).
    """
    anchor, keywords = (re.compile(p, re.IGNORECASE) for p in LABEL_PATTERNS[key])
    scored = [(len(anchor.findall(p)), len(keywords.findall(p)), -i, p)
              for i, p in enumerate(paras)]
    if not scored:
        return None
    anchor_hits, keyword_hits, _, para = max(scored)
    return para if anchor_hits or keyword_hits else None


def mentions(clause, key):
    """Whether a clause mentions the topic of a label at all (keyword pattern)."""
    return re.search(LABEL_PATTERNS[key][1], clause, re.IGNORECASE) is not None
