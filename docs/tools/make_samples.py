"""Sample/explainer images 23-27 for the slides."""
from diagram_kit import D, K


def code(d, x, y, w, h, title, lines, kind="grey", size=13.5, colors=None, title_kind=None):
    d.code(x, y, w, h, title, lines, title_kind or kind, size, colors)


GREEN, GREY, BLUE, PURPLE, RED, AMBER = "#2E7D32", "#9A9A95", "#2F6DB5", "#6B4FBB", "#B91C1C", "#B45309"

# ---------------------------------------------------------------- 23 inputs and outputs
d = D(1600, 1010, "What goes in and what comes out",
      "Two kinds of input (either or both) → the LicenseWise pipeline → the same result as readable text or as JSON")
d.text(40, 122, "INPUT", 14, "bold", "#888")
d.text(900, 122, "OUTPUT", 14, "bold", "#888")
d.box(40, 135, 760, 175, "Input 1 · Project description (plain text)", [
    "“A desktop app for small clinics to manage appointments.",
    " I'd like to be able to sell it.”",
    "",
    "Any length up to 4,000 characters · no license terms needed"], "kb", lsize=15)
code(d, 40, 330, 370, 330, "Input 2a · requirements.txt", [
    "requests>=2.31", "numpy==2.1.0  # arrays", "django", "pyqt5", "black[jupyter]", "-r other.txt          ← skipped", "this-package-does-not-exist-xyz"],
    colors={5: GREY}, title_kind="src", size=13)
code(d, 430, 330, 370, 330, "Input 2b · package.json (npm)", [
    "{", '  "name": "demo",', '  "dependencies": {', '    "react": "^18.0.0",', '    "lodash": "^4.17.0",',
    '    "left-pad": "1.3.0"', "  },", '  "devDependencies": {', '    "jest": "^29.0.0"   ← ignored', "  }", "}"],
    colors={7: GREY, 8: GREY, 9: GREY}, title_kind="src", size=13)
d.text(40, 690, "Also accepted: pyproject.toml ([project] dependencies). Files are only read, never run.", 14, color="#555")
d.box(40, 715, 760, 120, "Input checks", [
    "file type: requirements.txt · pyproject.toml · package.json only",
    "size ≤ 100 KB · must parse · description ≤ 4,000 characters"], "white", lsize=14)

d.p.append('<rect x="818" y="135" width="64" height="700" rx="12" fill="#EAF2FB" stroke="#2F6DB5" stroke-width="1.8"/>')
for i, w in enumerate(["L", "i", "c", "e", "n", "s", "e", "W", "i", "s", "e"]):
    d.text(850, 300 + i * 30, w, 20, "bold", "#2F6DB5", "middle")
d.arrow([(800, 222), (814, 222)])
d.arrow([(800, 495), (814, 495)])
d.arrow([(882, 300), (896, 300)])
d.arrow([(882, 720), (896, 720)])

code(d, 900, 135, 660, 395, "Output 1 · Readable result (UI cards / command line)", [
    "Requirements understood:",
    "  - Must allow commercial distribution and sale.",
    "  ! pyqt5 (GPL-3.0-only): requires a GPL-compatible",
    "    license",
    "",
    "1. GPL-3.0 — satisfies commercial sale and meets",
    "   pyqt5's GPL-3.0-only requirement",
    "   [verified]   You may charge any price or no price",
    "                for each copy you distribute …",
    "   [unverified] Any work you convey must be licensed",
    "                as a whole under GPL-3.0.",
    "2. AGPL-3.0 …   3. EPL-2.0 …",
    "Explanations are based on license text only.",
    "Not legal advice."], colors={2: AMBER, 3: AMBER, 5: "#111", 7: GREEN, 8: GREEN, 9: AMBER, 10: AMBER, 12: GREY, 13: GREY},
    title_kind="ok", size=13)
code(d, 900, 550, 660, 430, "Output 2 · JSON (API response / Download JSON)", [
    "{",
    '  "dependencies": [ {"name": "pyqt5",',
    '                     "license": "GPL-3.0-only"}, … ],',
    '  "requirements": [ {"text": "Must allow commercial …",',
    '                     "source": "description"}, … ],',
    '  "conflicts": [ {"dependency": "pyqt5", "issue": "…"} ],',
    '  "recommendations": [ {',
    '    "rank": 1, "spdx_id": "GPL-3.0",',
    '    "reason": "Satisfies commercial sale and …",',
    '    "claims": [ {',
    '      "text": "You may charge any price or no price …",',
    '      "clause_id": "C2",',
    '      "quote": "You may charge any price or no price …",',
    '      "status": "verified",',
    '      "nli": {"entailment": 0.994, "neutral": 0.006,',
    '              "contradiction": 0.0} }, … ] }, … ],',
    '  "disclaimer": "… This is not legal advice."',
    "}"], colors={13: GREEN}, title_kind="ok", size=13)
d.save("23_io_examples")

# ---------------------------------------------------------------- 24 choosealicense raw vs processed
d = D(1600, 900, "choosealicense.com: one raw file and the record we build from it",
      "Example: MIT. Green = kept · grey = dropped · blue = added by us")
code(d, 40, 120, 500, 750, "Raw file: _licenses/mit.txt", [
    "---", "title: MIT License", "spdx-id: MIT", "featured: true", "hidden: false", "",
    "description: A short and simple", "  permissive license with conditions", "  only requiring preservation of", "  copyright and license notices. …", "",
    "how: Create a text file (typically", "  named LICENSE …) …", "",
    "using:", "  Babel: https://github.com/…", "  .NET: https://github.com/…", "",
    "permissions:", "  - commercial-use", "  - modifications", "  - distribution", "  - private-use",
    "conditions:", "  - include-copyright", "limitations:", "  - liability", "  - warranty", "---", "",
    "MIT License", "Copyright (c) [year] [fullname]", "Permission is hereby granted, free …"],
    colors={1: GREEN, 2: GREEN, 3: GREY, 4: GREEN, 6: GREEN, 7: GREEN, 8: GREEN, 9: GREEN, 11: GREY, 12: GREY, 14: GREY, 15: GREY, 16: GREY,
            18: GREEN, 19: GREEN, 20: GREEN, 21: GREEN, 22: GREEN, 23: GREEN, 24: GREEN, 25: GREEN, 26: GREEN, 27: GREEN,
            30: GREEN, 31: GREEN, 32: GREEN}, title_kind="src", size=13)
d.arrow([(540, 495), (576, 495)])
code(d, 580, 120, 470, 750, "Processed record: licenses.json", [
    "{", '  "spdx_id": "MIT",', '  "key": "mit",', '  "title": "MIT License",', '  "nickname": "",',
    '  "description": "A short and simple …",', '  "hidden": false,', '  "permissions": [', '    "commercial-use",',
    '    "modifications", "distribution",', '    "private-use"],', '  "conditions": [', '    "include-copyright"],',
    '  "limitations": [', '    "liability", "warranty"],', '  "text": "MIT License\\n\\nCopyright …",',
    '  "intended_for": "software",', '  "osi_approved": true,', '  "in_scope": true,', '  "language": "en"', "}"],
    colors={1: GREEN, 2: GREEN, 3: GREEN, 4: GREEN, 5: GREEN, 6: GREEN, 7: GREEN, 8: GREEN, 9: GREEN, 10: GREEN, 11: GREEN, 12: GREEN,
            13: GREEN, 14: GREEN, 15: GREEN, 16: BLUE, 17: BLUE, 18: BLUE, 19: BLUE}, title_kind="kb", size=13)
d.arrow([(1050, 495), (1086, 495)])
uses = [("spdx_id", "the license's ID everywhere: catalogue, answer key, results", GREEN),
        ("title · description", "shown to Stage 1 in the license catalogue and in the UI", GREEN),
        ("permissions · conditions · limitations", "the ground truth: profiles (RQ1), claim templates (RQ2), copyleft class", GREEN),
        ("text", "split into clauses → Stage 2 evidence and the verifier", GREEN),
        ("intended_for · osi_approved · in_scope", "added by us: scope filter (47 → 34)", BLUE),
        ("language", "added by us: flags French-only CeCILL-2.1", BLUE),
        ("dropped: how · using · featured · note", "website content, not license facts", GREY)]
d.p.append('<rect x="1090" y="120" width="470" height="750" rx="10" fill="#FFFFFF" stroke="#C8C8C4" stroke-width="1.5"/>')
d.text(1106, 148, "What each field is for", 15.5, "bold")
y = 190
for field, use, col in uses:
    d.text(1106, y, field, 14.5, "bold", col)
    words, line, yy = use.split(), "", y + 24
    for w in words:
        if len(line) + len(w) > 50:
            d.text(1106, yy, line, 14, color="#444"); yy += 20; line = ""
        line += w + " "
    d.text(1106, yy, line, 14, color="#444")
    y = yy + 44
d.save("24_choosealicense_raw_vs_processed")

# ---------------------------------------------------------------- 25 clause split
d = D(1600, 900, "Splitting a license into clauses: before and after",
      "Example: AFL-3.0 section 1. Each list item becomes its own clause, with the sentence that introduces it attached")
code(d, 40, 120, 700, 620, "Before: raw license text", [
    "1) Grant of Copyright License. Licensor grants",
    "You a worldwide, royalty-free, non-exclusive,",
    "sublicensable license, for the duration of the",
    "copyright, to do the following:",
    "",
    "  a) to reproduce the Original Work in copies,",
    "  either alone or as part of a collective work;",
    "",
    "  b) to translate, adapt, alter, transform,",
    "  modify, or arrange the Original Work, thereby",
    "  creating derivative works (\"Derivative",
    "  Works\") based upon the Original Work;",
    "",
    "  c) to distribute or communicate copies of the",
    "  Original Work and Derivative Works to the",
    "  public, under any license of your choice …",
    "",
    "→ split at blank lines, the first paragraph says",
    "  nothing on its own (it stops at “following:”)"], colors={0: PURPLE, 1: PURPLE, 2: PURPLE, 3: PURPLE, 17: RED, 18: RED}, title_kind="src", size=14)
d.arrow([(740, 430), (786, 430)])
items = [("Clause C2", "a) to reproduce the Original Work in copies, either alone or as part of a collective work;", "copying"),
         ("Clause C3", "b) to translate, adapt, alter, transform, modify, or arrange the Original Work, thereby creating derivative works …", "modifications ✓ label"),
         ("Clause C4", "c) to distribute or communicate copies of the Original Work and Derivative Works to the public, under any license …", "distribution ✓ label")]
y = 120
for name, item, label in items:
    d.p.append(f'<rect x="790" y="{y}" width="770" height="190" rx="10" fill="#EAF5EA" stroke="#2E7D32" stroke-width="1.8"/>')
    d.text(806, y + 28, name, 15.5, "bold", GREEN)
    d.text(1544, y + 28, f"topic: {label}", 13.5, "bold", "#444", "end")
    d.text(806, y + 56, "Lead-in: “… 1) Grant of Copyright License. Licensor grants You a … license, …", 13.5, color=PURPLE)
    d.text(806, y + 76, "to do the following:”", 13.5, color=PURPLE)
    wl, line, yy = item.split(), "", y + 106
    for w in wl:
        if len(line) + len(w) > 82:
            d.text(806, yy, line, 14.5, "bold", "#222"); yy += 22; line = ""
        line += w + " "
    d.text(806, yy, line, 14.5, "bold", "#222")
    y += 206
d.text(40, 790, "Purple = the lead-in sentence attached to every item · bold = the list item itself.", 14.5, color="#444")
d.text(40, 816, "Now each clause is complete on its own, so it can be quoted as evidence and checked by the verifier (512-token limit).", 14.5, color="#444")
d.text(40, 842, "Result over all 33 English licenses: 812 clauses, median 329 characters.", 14.5, "bold", GREEN)
d.save("25_clause_split")

# ---------------------------------------------------------------- 26 profile and descriptions
d = D(1600, 800, "One profile and the descriptions written from it",
      "Profile P009 (3 requirements, 4 correct licenses) → three descriptions in different voices, each checked blind")
d.box(40, 120, 470, 290, "Profile P009", [
    "Requirements:", "• contributors must grant patent rights", "• the license must NOT give rights to the", "   project's name, logo or trademarks",
    "• people who modify the code should not", "   have to document what they changed", "", "Answer key (licenses that fit all three):",
    "MPL-2.0 · MS-PL · MS-RL · MulanPSL-2.0"], "kb", lsize=15, bold_lines=(0, 7, 8))
descs = [
    ("Hobbyist developer", "“I'm building an open-source CLI tool for organizing personal music libraries, and I want to ensure everyone who touches the code clearly gives permission to use my patents. It's important that no one uses the project's name or logo as their own brand … I don't want to burden my contributors with having to … mark which lines they edited.”"),
    ("Startup founder", "“Our company is releasing this data processing library … we need a clear patent grant for anyone using the software. We must strictly reserve all rights to our corporate name, trademarks, and logos … not requiring developers to maintain change logs or annotate their specific modifications.”"),
    ("University researcher", "“I am publishing this simulation engine from our lab … I want to make sure the patent rights are explicitly handed over to the users. … the lab's name and institutional logos are not covered by this release … we don't want any obligation for students to document exactly what they changed.”"),
]
y = 120
for persona, text in descs:
    d.p.append(f'<rect x="560" y="{y}" width="1000" height="200" rx="10" fill="#F1ECFB" stroke="#6B4FBB" stroke-width="1.8"/>')
    d.chip(576, y + 14, persona, "llm")
    d.text(1544, y + 32, "checker found: patent ✓  trademark ✓  no change notes ✓  → kept", 13.5, "bold", GREEN, "end")
    wl, line, yy = text.split(), "", y + 72
    for w in wl:
        if len(line) + len(w) > 112:
            d.text(576, yy, line, 14.5, color="#333"); yy += 22; line = ""
        line += w + " "
    d.text(576, yy, line, 14.5, color="#333")
    y += 216
d.arrow([(510, 265), (556, 265)])
d.text(40, 450, "Personas across all 235 descriptions", 16, "bold")
pers = [("startup founder", 29), ("university researcher", 25), ("freelance web developer", 12), ("hobbyist", 8), ("indie game developer", 7),
        ("researcher", 7), ("hobbyist developer", 6), ("academic researcher", 5), ("startup CTO", 5), ("student", 4)]
x, yy = 40, 470
for name, n in pers:
    label = f"{name} · {n}"
    w = 18 + 7.6 * len(label)
    if x + w > 510:
        x, yy = 40, yy + 34
    d.chip(x, yy, label, "llm")
    x += w + 8
d.text(40, yy + 60, "122 different persona labels in total.", 14.5, color="#444")
d.text(40, yy + 84, "The writer is asked for a different persona and project", 14.5, color="#444")
d.text(40, yy + 106, "type in each description; the labels are its own.", 14.5, color="#444")
d.save("26_profile_descriptions")

# ---------------------------------------------------------------- 27 NLI labelling
d = D(1600, 750, "How the NLI verifier labels a claim",
      "DeBERTa-v3-large reads the cited clause (premise) and the claim (hypothesis) and outputs three probabilities; the highest one becomes the badge")
d.box(40, 130, 520, 140, "Premise · cited clause (GPL-3.0, C2)", [
    "“You may charge any price or no price for each", "copy that you convey, and you may offer support",
    "or warranty protection for a fee.”"], "kb", lsize=15)
d.box(40, 300, 520, 140, "Hypothesis · claim written by Stage 2", [
    "“You may charge any price or no price for each", "copy you distribute, and you can also sell support",
    "or warranty services.”"], "llm", lsize=15)
d.box(640, 190, 260, 190, "NLI model", ["DeBERTa-v3-large", "pre-trained on public", "NLI datasets · runs", "locally · not trained by us"], "nli", lsize=14.5, center=True)
d.arrow([(560, 200), (636, 260)])
d.arrow([(560, 370), (636, 310)])
d.arrow([(900, 285), (956, 285)])
d.p.append('<rect x="960" y="130" width="600" height="310" rx="10" fill="#FFFFFF" stroke="#C8C8C4" stroke-width="1.5"/>')
d.text(976, 160, "Output: three probabilities (sum to 1)", 15.5, "bold")
for i, (lab, v, col) in enumerate([("entailment", 0.994, GREEN), ("neutral", 0.006, AMBER), ("contradiction", 0.0, RED)]):
    yy = 202 + i * 54
    d.text(976, yy + 15, lab, 15, color="#333")
    d.p.append(f'<rect x="1110" y="{yy}" width="330" height="20" rx="4" fill="#F1F1EF" stroke="#C8C8C4"/>')
    d.p.append(f'<rect x="1110" y="{yy}" width="{max(2, 330 * v)}" height="20" rx="4" fill="{col}"/>')
    d.text(1456, yy + 15, f"{v:.3f}", 15, "bold", col)
d.text(976, 395, "Highest = entailment  →  badge: ✓ Verified", 16, "bold", GREEN)
d.text(40, 500, "The rule (plus one check before it)", 16, "bold")
rules = [("0 · Quote check", "the quote must appear word for word in the cited clause — otherwise Unverified, no NLI run", "white"),
         ("entailment highest", "the clause supports the claim  →  ✓ Verified", "ok"),
         ("neutral highest", "the clause doesn't say  →  ? Unverified", "grey"),
         ("contradiction highest", "the clause says the opposite  →  ✗ Contradicted", "drop")]
x = 40
for t, l, kind in rules:
    d.box(x, 520, 370, 120, t, [], kind)
    wl, line, yy = l.split(), "", 580
    for w in wl:
        if len(line) + len(w) > 40:
            d.text(x + 14, yy, line, 14, color="#333"); yy += 20; line = ""
        line += w + " "
    d.text(x + 14, yy, line, 14, color="#333")
    x += 383
d.text(40, 690, "Another real case: AGPL-3.0 §6 vs “you must also make the full source code available at no extra cost” → contradiction 0.58 vs entailment 0.38", 14.5, color="#444")
d.text(40, 714, "→ shown as Contradicted, although the claim is broadly right: a known verifier error (slide 18b).", 14.5, color="#444")
d.save("27_nli_labeling")
