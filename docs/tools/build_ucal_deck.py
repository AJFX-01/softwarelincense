"""Build the LicenseWise Phase 2 deck on the UCalgary 'Conservative' template."""
import copy
import re
import shutil
import sys
import zipfile
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

HERE = Path(__file__).parent
PROJ = Path("/Users/ajegbomogunopeyemi/Desktop/Fall-2026-env/ensf-621/project")
FIG = PROJ / "docs" / "figures"
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "LicenseWise_Phase2.pptx"

# ---------- palette (from the template theme) ----------
RED = RGBColor(0xEE, 0x2C, 0x2A)
INK = RGBColor(0x26, 0x26, 0x26)
MUTED = RGBColor(0x59, 0x59, 0x59)
FAINT = RGBColor(0x76, 0x71, 0x6A)
ADDED = RGBColor(0xC2, 0x50, 0x1F)   # darker template orange, readable on white
CARD = RGBColor(0xF2, 0xF1, 0xEE)
HEAD = RGBColor(0x33, 0x33, 0x33)
BAND = RGBColor(0xF4, 0xF3, 0xF1)
RULE = RGBColor(0xD9, 0xD6, 0xD0)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

L, R = 0.62, 12.71          # content left/right edges (in)
W = R - L
TOP, BOTTOM = 1.80, 6.30     # content band
CAP_Y = 6.38

# ---------- open the .potx as a presentation ----------
src = PROJ / "Conservative.potx"
tmp = HERE / "template_as_pptx.pptx"
with zipfile.ZipFile(src) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
    for item in zin.infolist():
        data = zin.read(item.filename)
        if item.filename == "[Content_Types].xml":
            data = data.replace(b"presentationml.template.main+xml", b"presentationml.presentation.main+xml")
        zout.writestr(item, data)
prs = Presentation(tmp)

# drop the two sample slides
sldIdLst = prs.slides._sldIdLst
for sldId in list(sldIdLst):
    prs.part.drop_rel(sldId.rId)
    sldIdLst.remove(sldId)

LAY = {l.name: l for l in prs.slide_layouts}
TITLE_LAYOUT = LAY["Title Slide"]
CONTENT = LAY["Title and Content"]
STATEMENT = LAY["Statement slide"]
CLOSING = LAY["Concluding slide"]


# ---------- helpers ----------
def runs(par, text, size, color=INK, bold=False):
    """**bold**, ^^added (orange bold)^^ inline markup."""
    for tok in re.split(r"(\*\*.+?\*\*|\^\^.+?\^\^)", text):
        if not tok:
            continue
        r = par.add_run()
        f = r.font
        f.size = Pt(size)
        f.bold = bold
        f.color.rgb = color
        if tok.startswith("**"):
            r.text = tok[2:-2]
            f.bold = True
            if color == MUTED:
                f.color.rgb = INK
        elif tok.startswith("^^"):
            r.text = tok[2:-2]
            f.bold = True
            f.color.rgb = ADDED
        else:
            r.text = tok


def no_bullet(par):
    pPr = par._p.get_or_add_pPr()
    for tag in ("a:buNone", "a:buChar", "a:buAutoNum"):
        for el in pPr.findall(qn(tag)):
            pPr.remove(el)
    pPr.insert(0, pPr.makeelement(qn("a:buNone"), {}))
    pPr.set("marL", "0")
    pPr.set("indent", "0")


def bullet(par, char="•", color=RED, indent=0.25):
    pPr = par._p.get_or_add_pPr()
    pPr.set("marL", str(Inches(indent)))
    pPr.set("indent", str(-Inches(indent)))
    clr = pPr.makeelement(qn("a:buClr"), {})
    s = clr.makeelement(qn("a:srgbClr"), {"val": str(color)})
    clr.append(s)
    pPr.append(clr)
    pPr.append(pPr.makeelement(qn("a:buFont"), {"typeface": "Arial"}))
    pPr.append(pPr.makeelement(qn("a:buChar"), {"char": char}))


def numbered(par):
    pPr = par._p.get_or_add_pPr()
    pPr.set("marL", str(Inches(0.4)))
    pPr.set("indent", str(-Inches(0.4)))
    clr = pPr.makeelement(qn("a:buClr"), {})
    clr.append(clr.makeelement(qn("a:srgbClr"), {"val": str(RED)}))
    pPr.append(clr)
    pPr.append(pPr.makeelement(qn("a:buFont"), {"typeface": "+mj-lt"}))
    pPr.append(pPr.makeelement(qn("a:buAutoNum"), {"type": "arabicPeriod"}))


def text(slide, x, y, w, h, paras, size=18, color=MUTED, gap=8, anchor=MSO_ANCHOR.TOP,
         align=PP_ALIGN.LEFT, kind=None, name=None, bold=False):
    """paras: list of strings. kind: None | 'bullet' | 'number'."""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    if name:
        tb.name = name
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    for i, p in enumerate(paras):
        par = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        par.alignment = align
        if kind == "bullet":
            bullet(par)
        elif kind == "number":
            numbered(par)
        else:
            no_bullet(par)
        if i:
            par.space_before = Pt(gap)
        runs(par, p, size, color, bold)
    return tb


def card(slide, x, y, w, h, fill=CARD, name=None):
    s = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    s.adjustments[0] = 0.06 if w > 2 else 0.1
    s.fill.solid()
    s.fill.fore_color.rgb = fill
    s.line.fill.background()
    s.shadow.inherit = False
    if name:
        s.name = name
    return s


def card_text(slide, x, y, w, h, heading, paras, size=17, kind=None, head_size=22, pad=0.3,
              head_color=INK, gap=8):
    card(slide, x, y, w, h, name=f"Card: {heading}")
    yy = y + pad
    if heading:
        text(slide, x + pad, yy, w - 2 * pad, 0.45, [heading], size=head_size, color=head_color,
             bold=True)
        yy += 0.6
    text(slide, x + pad, yy, w - 2 * pad, h - (yy - y) - pad, paras, size=size, kind=kind, gap=gap)


def table(slide, x, y, w, rows, widths, size=14, row_h=0.4, head_size=None, bold_first=False,
          name="Table"):
    nr, nc = len(rows), len(rows[0])
    gs = slide.shapes.add_table(nr, nc, Inches(x), Inches(y), Inches(w), Inches(row_h * nr))
    gs.name = name
    tbl = gs.table
    tblPr = tbl._tbl.tblPr
    for attr in ("bandRow", "firstRow"):
        tblPr.set(attr, "0")
    # drop the table style so the template's red banding doesn't apply
    sid = tblPr.find(qn("a:tableStyleId"))
    if sid is not None:
        sid.text = "{5940675A-B579-460E-94D1-54222C63F5DA}"  # 'No Style, Table Grid'
    total = sum(widths)
    for j, cw in enumerate(widths):
        tbl.columns[j].width = Emu(int(Inches(w) * cw / total))
    for i, row in enumerate(rows):
        tbl.rows[i].height = Inches(min(row_h, 0.5) if i == 0 else row_h)
        for j, val in enumerate(row):
            c = tbl.cell(i, j)
            c.margin_left = c.margin_right = Inches(0.1)
            c.margin_top = c.margin_bottom = Inches(0.05)
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
            c.fill.solid()
            c.fill.fore_color.rgb = HEAD if i == 0 else (BAND if i % 2 == 0 else WHITE)
            tf = c.text_frame
            tf.word_wrap = True
            par = tf.paragraphs[0]
            no_bullet(par)
            if i == 0:
                runs(par, val, head_size or size, WHITE, bold=True)
            else:
                runs(par, val, size, INK, bold=(bold_first and j == 0))
            # thin rules
            tcPr = c._tc.get_or_add_tcPr()
            for edge in ("a:lnL", "a:lnR", "a:lnT", "a:lnB"):
                ln = tcPr.makeelement(qn(edge), {"w": "6350"})
                if edge in ("a:lnB",) or (edge == "a:lnT" and i == 0):
                    sf = ln.makeelement(qn("a:solidFill"), {})
                    sf.append(sf.makeelement(qn("a:srgbClr"), {"val": str(RULE)}))
                    ln.append(sf)
                else:
                    ln.append(ln.makeelement(qn("a:noFill"), {}))
                tcPr.insert(0, ln) if False else tcPr.append(ln)
            # tcPr children order: lnL lnR lnT lnB ... fill. Move fill after lines.
            fill = tcPr.find(qn("a:solidFill"))
            if fill is not None:
                tcPr.remove(fill)
                tcPr.append(fill)
    return gs


def image(slide, path, x, y, w, h, alt, align="center"):
    from PIL import Image
    iw, ih = Image.open(path).size
    scale = min(w / iw, h / ih)
    pw, ph = iw * scale, ih * scale
    px = x + (w - pw) / 2 if align == "center" else x
    py = y + (h - ph) / 2
    pic = slide.shapes.add_picture(str(path), Inches(px), Inches(py), Inches(pw), Inches(ph))
    pic.name = alt[:60]
    pic._element.nvPicPr.cNvPr.set("descr", alt)
    return pic


def caption(slide, s):
    text(slide, L, CAP_Y, 9.0, 0.3, [s], size=12, color=FAINT, name="Caption")


def add_slide_number(slide, layout):
    for sp in layout.placeholders:
        if sp.placeholder_format.type is not None and "SLIDE_NUMBER" in str(sp.placeholder_format.type):
            el = copy.deepcopy(sp._element)
            slide.shapes._spTree.append(el)
            return


def notes(slide, s):
    slide.notes_slide.notes_text_frame.text = s


def content_slide(title, note=None):
    s = prs.slides.add_slide(CONTENT)
    s.shapes.title.text = title
    for ph in list(s.placeholders):
        if ph.placeholder_format.idx == 1:
            ph._element.getparent().remove(ph._element)
    add_slide_number(s, CONTENT)
    if note:
        notes(s, note)
    return s


def stat(slide, x, y, w, big, label, big_size=40, label_size=15):
    text(slide, x, y, w, 0.7, [big], size=big_size, color=RED, bold=True)
    text(slide, x, y + 0.72, w, 0.5, [label], size=label_size, color=MUTED)


# =====================================================================
# 1 Cover
s = prs.slides.add_slide(TITLE_LAYOUT)
ph = {p.placeholder_format.idx: p for p in s.placeholders}
s.shapes.title.text = "LicenseWise"
ph[1].text = "Recommend, explain and verify software licenses with LLMs"
ph[10].text_frame.text = "Opeyemi Ajegbomogun · Okemawo Obadofin"
p2 = ph[10].text_frame.add_paragraph()
p2.text = "ENSF 621 · Phase 2 presentation"
ph[11].text = "University of Calgary · Fall 2026"
notes(s, "Phase 2 presentation. LicenseWise recommends a software license for a specific project, "
         "explains it with claims that quote the license text, and verifies every claim. We start with a "
         "one-slide recap of Phase 1, then the software solution, then the ML components, results, future "
         "work, conclusion and the live demo.")

# 2 Recap
s = content_slide(
    "Phase 1 built the pipeline and the test data",
    "One-slide recap of Phase 1. The two ML weak spots in the table are what Phase 2 targets: the recommender "
    "breaking stated requirements, and the verifier missing about a third of true claims. On the software "
    "side, the UI was a demo with saved results.")
text(s, L, TOP + 0.05, 5.0, 4.4, [
    "**Pipeline:** an LLM recommends 3 licenses → an LLM explains each with claims that quote a clause → "
    "an NLI model checks every claim",
    "**Expert-free data:** 34-license knowledge base · 77 requirement profiles → 190 project descriptions · "
    "729 clause–claim pairs, 146 hand-labelled (κ = 0.88)",
    "**Left open:** UI not connected to a backend · verifier missed true claims · recommender broke stated "
    "requirements",
], size=17, gap=16)
table(s, 6.0, TOP, R - 6.0, [
    ["Phase 1", "Result"],
    ["RQ1 Stage 1", "Hit@1 0.56 · Hit@3 0.74 (104 descriptions)"],
    ["RQ1 hard cases", "Hit@3 only 0.60 when 1–3 licenses fit"],
    ["RQ2 verifier", "Accuracy 0.815 · “verified” precision 0.944"],
    ["RQ2 weak spot", "Confirmed only 69% of true claims"],
    ["RQ3 preview", "100% quotes verbatim · 58% claims verified"],
    ["Top errors", "Trademark broken in 54% of picks · change notes 39%"],
], [1.7, 4.2], size=14, row_h=0.55, bold_first=True)
caption(s, "Phase 1 overview")

# 3 Problem
s = content_slide(
    "Developers need license advice they can check",
    "Why it matters: choosing a license is one of the first decisions in every open-source project, and a "
    "confident wrong answer about legal terms is worse than no answer. Our innovation is pairing the LLM with "
    "an independent verifier so every claim can be checked against the clause it cites.")
cw = (W - 0.4) / 2
card_text(s, L, TOP, cw, 4.45, "The pain", [
    "Licenses are chosen with little legal training; copyleft and patent terms are misread",
    "Two failures: a **wrong fit**, or a **clash** with a dependency’s license",
    "Quizzes are generic, scanners audit after the fact, lawyers are slow and costly",
    "LLM chatbots are fluent but confidently wrong, and can’t be checked",
], kind="bullet", gap=12)
card_text(s, L + cw + 0.4, TOP, cw, 4.45, "Our innovation", [
    "The LLM recommends only from a curated catalogue of 34 licenses",
    "Every claim must **quote a clause** of the license",
    "An **independent NLI verifier**, fine-tuned on license text, marks each claim verified, unverified or "
    "contradicted",
    "Evaluated without a legal expert: ground truth computed from public labels",
], kind="bullet", gap=12, head_color=RED)
caption(s, "Problem and solution")

# 4 Related work
s = content_slide(
    "Related work: none recommends and verifies",
    "Full citations are in the report’s related-work section. The point of this table is the last column: "
    "each line of work covers part of the problem, but none both recommends a license for a specific project "
    "before coding and checks its own explanation against the license text.")
table(s, L, TOP, W, [
    ["Area", "Representative work", "What it does", "What’s missing"],
    ["Developer studies", "Almeida et al. 2017; Wu et al. 2024", "Show developers misread terms",
     "Motivation; no tool"],
    ["Identification", "Ninka; ScanCode; LtRecognizer", "Find the license in a file", "Identify, don’t recommend"],
    ["Compatibility", "Kapitsaki et al. (SPDX); LiDetector; OSADL", "Detect conflicts in existing code",
     "Audit after coding; no “why”"],
    ["Decision guides", "choosealicense.com", "A few generic paths", "Not project-specific"],
    ["Faithfulness / NLI", "SummaC; TRUE; MNLI; ANLI", "Flag unsupported generated text",
     "Not applied to license text"],
    ["Grounding", "RAG (Lewis et al. 2020)", "Ground output in passages", "No per-claim verdict"],
], [2.2, 3.6, 3.2, 3.1], size=15, row_h=0.6, bold_first=True)
caption(s, "Related work")

# 5 Gap (statement layout)
s = prs.slides.add_slide(STATEMENT)
ph = s.placeholders[10]
tf = ph.text_frame
tf.text = ""
p = tf.paragraphs[0]
runs(p, "No tool both recommends a license for a specific project before coding and verifies its own "
        "explanation against the license text.", 36, RED, bold=True)
p.line_spacing = 1.0
p = tf.add_paragraph()
p.space_before = Pt(24)
runs(p, "LicenseWise combines all three: project-specific recommendation, clause-quoting explanation, and a "
        "per-claim NLI verdict the developer can check.", 22, MUTED)
p.line_spacing = 1.0
notes(s, "This is the gap statement that motivates the research questions on the next slide.")

# 6 RQs
s = content_slide(
    "Three research questions, refined for Phase 2",
    "The Phase 1 questions are unchanged except for the orange additions: RQ1 now asks whether grounding the "
    "model in license labels helps, and RQ2 now covers a fine-tuned verifier as well as off-the-shelf ones.")
cw = (W - 0.6) / 3
rq = [
    ("RQ1", "**Requirement-to-license mapping.** To what extent can an open-weight LLM, conditioned on a curated "
            "license catalogue, map natural-language project requirements to licenses that satisfy them, how "
            "does accuracy vary with specificity, ^^and how much does grounding it in the catalogue’s license "
            "labels help?^^"),
    ("RQ2", "**Claim verification.** How reliably can NLI models, ^^off the shelf and adapted to license text "
            "by fine-tuning,^^ verify LLM-generated claims against the clauses they cite, on human-validated "
            "clause–claim pairs?"),
    ("RQ3", "**Explanation faithfulness.** To what extent are LLM-generated explanations grounded in the cited "
            "license text, and how does NLI verification change the claims shown compared with an unverified "
            "baseline?"),
]
for i, (k, body) in enumerate(rq):
    x = L + i * (cw + 0.3)
    card(s, x, TOP, cw, 4.45, name=f"Card: {k}")
    text(s, x + 0.3, TOP + 0.3, cw - 0.6, 0.6, [k], size=30, color=RED, bold=True)
    text(s, x + 0.3, TOP + 1.0, cw - 0.6, 3.3, [body], size=16)
caption(s, "Research questions · orange = added in Phase 2")

# 7 Shaw
s = content_slide(
    "The RQs in Shaw’s research categories",
    "Mapped to Shaw’s categories of research questions, results and validation, as the assignment asks.")
table(s, L, TOP, W, [
    ["", "Question type", "Result type", "Validation"],
    ["RQ1", "Method of development: can an LLM plus a catalogue map requirements to licenses?",
     "Procedure or technique (prompt v1 → v2)",
     "Analysis: paired experiment on 104 descriptions with computed answer keys"],
    ["RQ2", "Method for analysis: can NLI check claims about license text?",
     "Technique and empirical model (fine-tuned verifier)",
     "Analysis: grouped cross-validation, human-labelled test set"],
    ["RQ3", "Characterisation of a particular system", "Specific solution (the verified pipeline)",
     "Evaluation: verified vs unverified claims on real runs"],
], [0.8, 4.0, 3.3, 4.0], size=16, row_h=1.0, bold_first=True)
caption(s, "Shaw, M. Writing good software engineering research papers. ICSE 2003")

# 8 What changed
s = content_slide(
    "What changed in Phase 2",
    "The whole of Phase 2 on one slide: three software changes and three ML changes. The following slides go "
    "through each.")
table(s, L, TOP, W, [
    ["Area", "Phase 1", "Phase 2", "Why"],
    ["UI ↔ backend", "UI showed saved examples", "**FastAPI backend**, live runs, history",
     "A real tool and a real demo"],
    ["Storage", "None", "**SQLite** job history", "Survives restarts; queryable"],
    ["Engineering", "Manual checks", "**27 tests, ruff, GitHub Actions** on development and main",
     "CI/CD; catch regressions"],
    ["Verifier", "Off-the-shelf DeBERTa", "**Threshold tuned**, then **top 4 layers fine-tuned**",
     "Base model missed 31% of true claims"],
    ["Stage 1 prompt", "Catalogue = title + description",
     "**v2:** + license labels; check every requirement, then rank",
     "Most wrong picks broke a stated requirement"],
    ["Stage 1 model", "gpt-oss-120b", "Compared with **gpt-oss-20b**", "Cost vs quality"],
], [1.9, 2.8, 4.2, 3.2], size=15, row_h=0.62, bold_first=True)
caption(s, "Software solution")

# 9 Architecture
s = content_slide(
    "Phase 2 architecture",
    "The Phase 1 design already planned a web UI talking to a FastAPI backend. Phase 2 built it, with a REST "
    "shape that suits long runs: post a request, get a job id back immediately, and poll for progress. The job "
    "store moved from an in-memory cache to SQLite. In the pipeline, Stage 1 and the verifier changed. The rules "
    "engine from the original proposal is still future work.")
image(s, FIG / "p2_07_system_design_v2.png", L, TOP - 0.05, 7.3, 4.55,
      "Phase 2 system design: web UI, FastAPI backend with SQLite, and the seven-step pipeline, with new and "
      "changed parts marked", align="left")
text(s, 8.25, TOP + 0.1, R - 8.25, 4.4, [
    "**Built as planned:** web UI → FastAPI → pipeline",
    "**Changed:** REST shape with polling, SQLite job store, Stage 1 prompt v2, fine-tuned verifier",
    "**Why async jobs:** a run takes 30 s to 5 min on the free tier, so POST returns 202 + a job id at once",
    "**Not built:** rules engine and OSADL compatibility check (future work)",
], size=16, gap=14)
caption(s, "Architecture evolution · green = new · amber = changed")

# 10 Tech stack
s = content_slide(
    "Implementation: tech stack",
    "Everything runs on free tiers and a laptop: Groq’s free tier for the LLM, and the verifier on Apple MPS "
    "locally.")
table(s, L, TOP, W, [
    ["Layer", "Technology", "Notes"],
    ["Repository", "GitHub: AJFX-01/softwarelincense", "Branches development → main"],
    ["Front end", "React 19, TypeScript, Vite", "New recommendation · History · Licenses"],
    ["Backend", "FastAPI + Uvicorn, Python 3.14", "5 endpoints, 1 worker thread, input validation"],
    ["Database", "SQLite (Python standard library)", "Job history, identical-input reuse"],
    ["LLM", "gpt-oss-120b via Groq (open-weight)", "Strict JSON-schema output; Stage 1 and 2"],
    ["Verifier", "DeBERTa-v3-large NLI, PyTorch, Transformers", "Top 4 of 24 layers fine-tuned; runs locally"],
    ["Quality", "pytest, ruff, oxlint, tsc", "Run locally and in CI"],
    ["Reproducibility", "Pinned requirements, seeds, project log", "Every decision recorded with its reason"],
], [2.1, 5.0, 5.0], size=15, row_h=0.49, bold_first=True)
caption(s, "Implementation")

# 11 Database
s = content_slide(
    "SQLite stores every run",
    "The result is kept as one JSON column because its nested shape is still evolving; the fields we query on "
    "are real columns.")
card(s, L, TOP, 5.6, 4.45, name="Card: jobs table")
text(s, L + 0.3, TOP + 0.3, 5.0, 0.45, ["Table jobs"], size=22, color=INK, bold=True)
text(s, L + 0.3, TOP + 0.95, 5.0, 3.4, [
    "**id** TEXT primary key",
    "**input_key** TEXT: SHA-256 of model, description, manifest, verify",
    "**status** TEXT: queued, running, done, failed",
    "**created_at** TEXT, indexed",
    "**data** TEXT: the full job and result as JSON",
], size=16, kind="bullet", gap=10)
text(s, L + 6.1, TOP + 0.15, W - 6.1, 4.3, [
    "**Why SQLite:** no server to run for a single-user tool; atomic writes; history queryable by status and "
    "time; in the Python standard library",
    "**Reuse:** an identical request returns the finished result instead of spending LLM quota again",
    "**Restart-safe:** jobs left running are marked failed with a clear message; Phase 1 job files are "
    "imported once",
], size=17, gap=18)
caption(s, "Database")

# 12 CI/CD
s = content_slide(
    "Every push is linted, tested and built",
    "Two jobs run on every push and pull request: backend runs ruff and 27 pytest tests; ui runs oxlint, the "
    "TypeScript type-check and the production build. The tests mock the LLM and the NLI model, so CI needs no "
    "API key, no GPU and no model download. Show the green Actions run and the merged pull request here during "
    "the demo.")
image(s, FIG / "p2_08_cicd.png", L, TOP - 0.1, W, 3.55,
      "CI/CD flow: push to development triggers GitHub Actions jobs for backend and UI; a pull request with "
      "green checks merges into main")
half = (W - 0.4) / 2
text(s, L, 5.45, half, 0.85, ["**Two branches:** development for integration; main only through a pull "
                               "request with green checks"], size=16)
text(s, L + half + 0.4, 5.45, half, 0.85, ["**Tests found a bug:** the API’s worker pool could not restart "
                                            "in one process; fixed"], size=16)
caption(s, "CI/CD and GitHub")

# 13 UI <-> API
s = content_slide(
    "How the UI talks to the backend",
    "The UI is a React app; in development, Vite proxies /api to the FastAPI server, so no extra CORS setup is "
    "needed.")
table(s, L, TOP, W, [
    ["UI action", "API call", "What the user sees"],
    ["Open the app", "GET /api/health, every 30 s", "“Backend connected” or “offline”"],
    ["Press Recommend", "POST /api/recommendations → 202 + job id", "Run starts, or an identical past run is reused"],
    ["While running", "GET /api/recommendations/{id}, every 1.5 s", "Live step and queue position"],
    ["Open History", "GET /api/recommendations", "Past runs: top pick, claims verified"],
    ["Open Licenses", "GET /api/licenses", "34 licenses, labels, copyleft level"],
], [2.3, 5.0, 4.8], size=15, row_h=0.6, bold_first=True)
text(s, L, 5.65, W, 0.6, ["Clear errors for a Groq rate limit, a missing API key, or an invalid or empty manifest "
                          "(rejected with 422 before any LLM call)."], size=16)
caption(s, "UI integration")

# 14 ML changes
s = content_slide(
    "What changed in data, training and evaluation",
    "We did not label any new data in Phase 2. The main data change is that the verifier test set is now also "
    "training data, which is only fair because every prediction we report comes from a fold that never saw "
    "that pair.")
cw, ch = (W - 0.3) / 2, (4.45 - 0.3) / 2
cards = [
    ("Data", "No new labelling: the 729 clause–claim pairs became training data via 5-fold cross-validation. "
             "Target = human label where it exists (146), else the automatic label (97.9% agree with humans)."),
    ("Leakage control", "Folds grouped by license (main), and by claim template as a stress test: every "
                        "wording of, e.g., “commercial use allowed” held out together."),
    ("Transformation", "Outputs of the frozen lower layers are computed once and cached, so training touches "
                       "only the top layers and fits a 16 GB laptop."),
    ("Evaluation", "Same metrics and the same 104 Stage 1 descriptions as Phase 1, so every comparison is "
                   "paired and directly comparable."),
]
for i, (h, b) in enumerate(cards):
    x = L + (i % 2) * (cw + 0.3)
    y = TOP + (i // 2) * (ch + 0.3)
    card_text(s, x, y, cw, ch, h, [b], size=17, head_size=20, pad=0.25)
caption(s, "ML components")


def fig_slide(title, fig, alt, bullets, cap, note, img_w=7.4, size=16):
    s = content_slide(title, note)
    image(s, FIG / fig, L, TOP, img_w, 4.45, alt, align="left")
    tx = L + img_w + 0.35
    text(s, tx, TOP + 0.1, R - tx, 4.35, bullets, size=size, gap=14)
    caption(s, cap)
    return s


# 15 Verifier configs
fig_slide(
    "Fine-tuning 4 layers wins", "p2_02_verifier_configs.png",
    "Bar chart of accuracy, verified precision and true claims confirmed for five verifier configurations on "
    "146 human-labelled pairs",
    ["**Base, argmax:** Phase 1 baseline",
     "**Base, t = 0.10:** small gain from a tuned threshold",
     "**K = 2 vs K = 4:** 4 layers learn more; 8 did not fit in memory",
     "**Template held out:** the honest score for unseen wording"],
    "RQ2 · configurations explored · 146 human-labelled pairs · dashed line = 0.90 precision target",
    "Five configurations on the same 146 human-labelled pairs. Accuracy goes from 0.815 for the Phase 1 "
    "baseline to 0.925 for the 4-layer fine-tune, verified precision from 0.944 to 0.978, and the share of true "
    "claims confirmed from 0.694 to 0.918. RoBERTa-large was compared in Phase 1 and stayed behind.")

# 16 Threshold
fig_slide(
    "A tuned threshold helps a little", "p2_01_threshold_curve.png",
    "Line chart of entailment precision, entailment recall and macro-F1 against the threshold on 583 tuning "
    "pairs, with the chosen threshold 0.10 marked",
    ["**Rule:** “verified” if P(entailment) ≥ t",
     "**Chosen on** the 583 pairs without human labels: best macro-F1 with precision ≥ 0.90 → t = 0.10",
     "**On the human set:** accuracy 0.815 → 0.829; true claims confirmed 69% → 76%",
     "Not enough on its own → fine-tuning"],
    "RQ2 · hyperparameter: decision threshold",
    "The threshold was picked without looking at the human-labelled pairs, so the human-set numbers are a fair "
    "test. Lowering the threshold confirms more true claims, but precision falls below 0.90 at t = 0.05. The "
    "fine-tuned model doesn’t need a threshold: its argmax precision is already 0.93 to 0.98.")

# 17 Fine-tune setup
s = content_slide(
    "Fine-tuning hyperparameters and why",
    "Only the top layers are trained, so the outputs of the bottom 20 layers never change. We compute them once, "
    "cache them, and train the top 4 layers on top of the cache. A sanity check reproduced the base model’s "
    "predictions on all 729 pairs before training.")
table(s, L, TOP, W, [
    ["Choice", "Value", "Why"],
    ["Base model", "DeBERTa-v3-large NLI", "Best Phase 1 verifier"],
    ["Trainable", "Top K = 4 of 24 layers + classifier",
     "K = 2 under-fits; K = 8 out of memory; 729 pairs too few for full fine-tuning"],
    ["Optimiser", "AdamW, lr 2e-5, weight decay 0.01, 10% warm-up, clip 1.0", "Standard for DeBERTa fine-tuning"],
    ["Epochs, batch", "3 epochs, batch 8, length-grouped", "Small data; less padding"],
    ["Validation", "5-fold grouped CV, out-of-fold predictions", "Every pair scored by a model that never saw it"],
    ["Final model", "Retrained on all 729 pairs, about 4 min", "Deployed in the app"],
], [1.8, 5.2, 5.1], size=14, row_h=0.48, bold_first=True)
text(s, L, 5.75, W, 0.6, ["**Laptop-friendly:** cached frozen layers (no 13 GB swapping); clearing the GPU cache "
                          "cut an epoch from 33 min to 63 s."], size=16)
caption(s, "RQ2 · fine-tuning setup")

# 18 Verifier results
s = content_slide(
    "Verifier errors fall from 27 to 11 of 146",
    "Only one neutral claim is marked verified and no contradiction is marked verified, so the faithfulness "
    "requirement holds. The real-claim preview re-verified saved pipeline runs with both models; it is a "
    "preview, since those claims are not human-labelled.")
image(s, FIG / "p2_03_confusion_base_vs_finetuned.png", L, TOP, 7.6, 3.55,
      "Two confusion matrices: base DeBERTa with accuracy 0.815 and fine-tuned with accuracy 0.925", align="left")
sx = L + 7.95
stat(s, sx, TOP + 0.05, R - sx, "0.815 → 0.925", "accuracy", big_size=34)
stat(s, sx, TOP + 1.15, R - sx, "69% → 92%", "of true claims confirmed", big_size=34)
stat(s, sx, TOP + 2.3, R - sx, "0.944 → 0.978", "“verified” precision (target ≥ 0.90)", big_size=34)
text(s, L, 5.55, W, 0.7, ["**On 37 real Stage 2 claims** (not human-labelled): verified 24 → 32, unverified "
                          "11 → 4, contradicted 2 → 1; all 8 changes read as correct."], size=16)
caption(s, "RQ2 · results vs baseline · license-held-out cross-validation, 146 human-labelled pairs")

# 19 Memorisation
fig_slide(
    "Most verifier gains hold for unseen wording", "p2_04_template_memorisation.png",
    "Dot plot of entailment recall per claim label for the base model, fine-tuned with the template seen, and "
    "fine-tuned with the template unseen",
    ["**Test:** hold out every wording of a claim template, so the model never sees it in training",
     "**Generalises:** patent use 0.41 → 0.94 · trademark 0.55 → 1.00 · warranty 0.75 → 0.97, even unseen",
     "**Partly memorised:** commercial use 0.21 → 1.00 when seen, only 0.33 unseen",
     "**New cost:** 1 contradiction marked verified on unseen wording (base: 0)",
     "Honest estimate for new claims: **accuracy 0.911, precision 0.933**"],
    "RQ2 · generalisation check · entailment recall per label, all 729 pairs",
    "Our claim pairs were generated from templates, so a model could simply memorise the wording. Holding out "
    "whole templates tests that. Most labels keep their gain, but commercial use does not, which is why we "
    "report both scores and list paraphrased training claims as future work.",
    img_w=6.2, size=15)

# 20 Stage 1 configs
s = content_slide(
    "License labels in the prompt lift every metric",
    "Prompt v2 adds each license’s permissions, conditions and limitations to the catalogue, and asks the model "
    "to list the requirements, keep only licenses that satisfy all of them, then rank. All three configurations "
    "ran on the same descriptions as the Phase 1 baseline. These are interim numbers on 68 descriptions; update "
    "them when the full runs finish.")
image(s, FIG / "p2_05_stage1_configs.png", L, TOP, 6.9, 3.45,
      "Grouped bar chart of Hit@1, Hit@3 and Precision@3 for prompt v1 and v2 on gpt-oss-120b and prompt v1 on "
      "gpt-oss-20b", align="left")
table(s, L + 7.2, TOP + 0.3, R - L - 7.2, [
    ["Config", "Hit@1", "Hit@3", "P@3"],
    ["v1 · 120b (Phase 1)", "0.59", "0.77", "0.59"],
    ["**v2 · 120b**", "**0.88**", "**0.94**", "**0.87**"],
    ["v1 · 20b", "0.56", "0.74", "0.58"],
], [2.2, 0.9, 0.9, 0.9], size=15, row_h=0.55)
text(s, L, 5.4, W, 0.9, ["**One** new prompt, designed from Phase 1 errors before any new results, so no tuning "
                         "on the test set. v2 costs ~6k tokens per description vs ~4.2k. The 20b model uses ~12% "
                         "fewer tokens but is slightly worse."], size=16)
text(s, L, CAP_Y, W, 0.3, ["RQ1 · configurations explored · **interim: 68 paired descriptions; final numbers on "
                           "all 104 to follow**"], size=12, color=FAINT, name="Caption")
for r_ in s.shapes[-1].text_frame.paragraphs[0].runs:
    if r_.font.bold:
        r_.font.color.rgb = ADDED

# 21 Stage 1 fails
s = content_slide(
    "Labels fixed explicit rules, not copyleft level",
    "Weak copyleft means LGPL or MPL style: changes to the library’s own files must stay open, but it can be "
    "combined with closed code. Only two to four licenses fit those requests, and the v2 prompt never explained "
    "the weak-copyleft labels. We did not patch the prompt after seeing these results, because that would be "
    "tuning on the test set; it is future work.")
image(s, FIG / "p2_06_stage1_violations.png", L, TOP, 6.9, 3.45,
      "Horizontal bar chart of the share of recommendations that break each stated constraint, for the three "
      "Stage 1 configurations", align="left")
table(s, L + 7.2, TOP, R - L - 7.2, [
    ["Picks breaking…", "v1", "v2"],
    ["Trademark", "0.51", "**0.04**"],
    ["Change notes", "0.33", "**0.10**"],
    ["Network use", "0.13", "**0.01**"],
    ["Copyleft level", "0.28", "0.26"],
], [2.6, 1.0, 1.0], size=15, row_h=0.5)
text(s, L + 7.2, TOP + 2.75, R - L - 7.2, 1.7, ["Every remaining copyleft miss asks for **weak copyleft** plus "
                                                "another requirement; the model falls back to permissive "
                                                "licenses such as Apache-2.0."], size=16)
caption(s, "RQ1 · error analysis · interim: 68 paired descriptions")

# 22 Requirements
s = content_slide(
    "Every Phase 1 requirement is now met",
    "The functional and non-functional requirements from Phase 1, checked against Phase 2 results.")
table(s, L, TOP - 0.05, W, [
    ["Requirement", "Target", "Phase 2"],
    ["FR1/FR2 Input", "Description, manifest, or both", "Met: UI and API, validated"],
    ["FR4 Recommend 3 licenses", "Fit stated requirements", "Met: Hit@3 0.94 (Phase 1: 0.74)"],
    ["FR5 Explain with clauses", "Every claim quotes a clause", "Met"],
    ["FR6 Verify each claim", "Three verdicts", "Met: fine-tuned verifier"],
    ["NFR Faithfulness", "“Verified” precision ≥ 0.90", "Met: 0.978 (0.933 unseen wording)"],
    ["NFR Latency", "Under 5 min on free tier", "Met: ~30–35 s in test runs"],
    ["NFR Cost", "Free tier + local model", "Met"],
    ["NFR Maintainability", "Modular, reproducible", "Met: tests, CI, pinned deps, log"],
    ["NFR Security", "Size and type limits; never run input", "Met: checked before any LLM call"],
], [3.3, 4.1, 4.7], size=14, row_h=0.445, bold_first=True)
caption(s, "Results vs requirements · Hit@3 is interim (68 descriptions)")

# 23 Strengths / weaknesses
s = content_slide(
    "Strengths and weaknesses",
    "Strengths and weaknesses of the Phase 2 system, from the results on the previous slides.")
cw = (W - 0.4) / 2
card_text(s, L, TOP, cw, 4.45, "Strengths", [
    "Correct license in the top 3 for ~94% of descriptions; top pick ~88% (Phase 1: 56%)",
    "“Verified” is reliable: precision 0.98, and 92% of true claims confirmed",
    "Every claim traceable to an exact clause",
    "Runs on free tiers and a laptop; tested, CI-checked, reproducible",
], kind="bullet", size=16, gap=10)
card_text(s, L + cw + 0.4, TOP, cw, 4.45, "Weaknesses", [
    "Weak-copyleft requests still get permissive picks",
    "Some verifier gain is memorised wording; 1 false “verified” on unseen wording",
    "Test descriptions are LLM-written, not from real developers",
    "Real Stage 2 claims only previewed, not human-labelled",
    "v2 prompt costs ~40% more tokens",
], kind="bullet", size=16, gap=10)
caption(s, "Stage 1 figures interim (68 descriptions)")

# 24 Findings
s = content_slide(
    "Four things Phase 2 showed",
    "Impact: a developer gets a project-specific license choice with explanations they can check clause by "
    "clause, instead of a generic quiz or an unverifiable chatbot answer.")
cw = (W - 0.9) / 4
finds = [
    ("0.59 → 0.88", "**Grounding beats model size.** License labels lifted top-pick accuracy; a smaller model "
                    "did worse."),
    ("69% → 92%", "**Domain adaptation fixes the blind spot.** True claims confirmed, with precision still "
                  "above 0.9."),
    ("4 minutes", "**Cheap enough for a laptop.** Caching frozen layers turned an out-of-memory job into a "
                  "short run."),
    ("0 experts", "**Expert-free evaluation works.** Computed answer keys and a small human-checked set gave "
                  "clear, paired comparisons."),
]
for i, (big, body) in enumerate(finds):
    x = L + i * (cw + 0.3)
    card(s, x, TOP, cw, 4.45, name=f"Card: finding {i + 1}")
    text(s, x + 0.25, TOP + 0.35, cw - 0.5, 0.7, [big], size=30, color=RED, bold=True)
    text(s, x + 0.25, TOP + 1.3, cw - 0.5, 3.0, [body], size=18)
caption(s, "Key findings · Stage 1 figure interim (68 descriptions)")

# 25 Future work
s = content_slide(
    "Next steps, from the weaknesses",
    "Each item maps to a weakness on the previous slides.")
table(s, L, TOP, W, [
    ["Weakness", "Next step"],
    ["Weak-copyleft picks", "Explain the copyleft labels in the prompt; re-test on new descriptions"],
    ["Memorised claim wording", "Paraphrase claim templates for fine-tuning"],
    ["Real claims not labelled", "Human-label real Stage 2 claims (full RQ3)"],
    ["Dependency conflicts", "Rules engine with the OSADL compatibility matrix"],
    ["Token cost of v2", "Compact catalogue (labels only); self-consistency voting"],
    ["Synthetic test data", "User study with developers on clarity and trust"],
    ["Scope", "More licenses (non-OSI, custom); deploy behind sign-in"],
], [4.0, 8.1], size=16, row_h=0.55, bold_first=True)
caption(s, "Future work")

# 26 Conclusion
s = content_slide(
    "Project-specific license advice you can check",
    "The 0.56 is the Phase 1 top-pick accuracy on all 104 descriptions; the ~0.88 is the interim v2 figure on "
    "the paired sample.")
text(s, L, TOP + 0.05, W - 0.5, 4.4, [
    "**Phase 2 delivered** a connected web app (FastAPI, SQLite, React), CI/CD on two branches, a fine-tuned "
    "verifier, and a label-grounded recommender.",
    "**Against the baseline,** top-pick accuracy rose from 0.56 to ~0.88, and verifier accuracy from 0.815 to "
    "0.925 with “verified” precision 0.98.",
    "**Overall,** an LLM paired with an independent, domain-adapted verifier gives license advice a developer "
    "can check clause by clause, and it can be evaluated rigorously without a legal expert.",
    "Not legal advice, but a faster and transparent first step.",
], size=20, gap=18)
caption(s, "Conclusion · Stage 1 figure interim (68 descriptions)")

# 27 Demo
s = content_slide(
    "Live walkthrough",
    "Before presenting: start the API with uvicorn and the UI with pnpm dev, check the backend pill shows "
    "connected, and run the demo inputs once so they are in History as a fallback.")
text(s, L, TOP + 0.05, W - 0.5, 3.9, [
    "**Describe:** a SaaS analytics library whose users must share improvements → watch the live steps → "
    "AGPL-3.0 expected first",
    "**Evidence:** open a claim → quoted clause highlighted, NLI scores",
    "**Manifest:** upload a requirements.txt with pyqt5 → GPL-3.0 dependency flagged; picks respect it",
    "**Reuse:** submit the same input again → returned instantly, no new LLM call",
    "**History:** reopen a past run from SQLite",
    "**GitHub:** green Actions run on development → pull request → main",
], size=18, kind="number", gap=10)
text(s, L, 5.75, W, 0.5, ["Backup if Groq is rate-limited during the demo: saved runs in History."], size=15,
     color=FAINT)
caption(s, "Demo")

# 28 Contributions
s = content_slide("Individual contributions", "To be filled in by the team.")
cw = (W - 0.4) / 2
for i, name in enumerate(["Opeyemi Ajegbomogun", "Okemawo Obadofin"]):
    card_text(s, L + i * (cw + 0.4), TOP, cw, 4.45, name, ["[Contributions]"], size=17)
caption(s, "Team")

# 29 Questions (concluding layout)
s = prs.slides.add_slide(CLOSING)
ph = {p.placeholder_format.idx: p for p in s.placeholders}
s.shapes.title.text = "Questions?"
ph[1].text = "Thank you for listening"
ph[10].text_frame.text = "Opeyemi Ajegbomogun · Okemawo Obadofin"
ph[10].text_frame.add_paragraph().text = "github.com/AJFX-01/softwarelincense"
notes(s, "Thank the audience and take questions.")

prs.core_properties.title = "LicenseWise Phase 2"
prs.core_properties.author = "Opeyemi Ajegbomogun, Okemawo Obadofin"
prs.save(OUT)
tmp.unlink()
print("saved", OUT, len(prs.slides), "slides")
