"""Small SVG helper used to draw the slide diagrams in docs/figures/.

Render an SVG to PNG with headless Chrome, e.g.:
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless --hide-scrollbars \
      --window-size=W,H --screenshot=out.png file:///path/to/figure.svg
"""
from html import escape
from pathlib import Path

FIG = Path(__file__).resolve().parent.parent / "figures"
FONT = "Helvetica, Arial, sans-serif"
MONO = "JetBrains Mono, Menlo, Consolas, monospace"
K = {  # kind -> (fill, stroke)
    "src": ("#FFF4E5", "#D9822B"), "kb": ("#EAF2FB", "#2F6DB5"), "llm": ("#F1ECFB", "#6B4FBB"),
    "nli": ("#EAF5EA", "#2E7D32"), "grey": ("#F4F4F2", "#8A8A85"), "white": ("#FFFFFF", "#9AA5B1"),
    "drop": ("#FDF0F0", "#B91C1C"), "ok": ("#EAF5EA", "#2E7D32"), "blue": ("#EAF2FB", "#2F6DB5"),
}


class D:
    def __init__(self, w, h, title, subtitle):
        self.w, self.h, self.p = w, h, []
        self.text(40, 50, title, 28, "bold")
        self.text(40, 80, subtitle, 16, color="#555")

    def text(self, x, y, s, size=15, weight="normal", color="#222", anchor="start", italic=False, font=FONT):
        st = ' font-style="italic"' if italic else ""
        self.p.append(f'<text x="{x}" y="{y}" font-family="{font}" font-size="{size}" font-weight="{weight}" '
                      f'fill="{color}" text-anchor="{anchor}" xml:space="preserve"{st}>{escape(s)}</text>')

    def wrap(self, x, y, s, width_chars, size=14.5, color="#333", weight="normal", step=None):
        line, yy = "", y
        for w in s.split():
            if line and len(line) + len(w) > width_chars:
                self.text(x, yy, line.rstrip(), size, weight, color)
                yy += step or size + 7
                line = ""
            line += w + " "
        self.text(x, yy, line.rstrip(), size, weight, color)
        return yy

    def box(self, x, y, w, h, title, lines=(), kind="white", dashed=False, tsize=16, lsize=14, center=False, bold_lines=()):
        fill, stroke = K[kind]
        dash = ' stroke-dasharray="7 5"' if dashed else ""
        self.p.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{fill}" stroke="{stroke}" stroke-width="1.8"{dash}/>')
        ax, anc = (x + w / 2, "middle") if center else (x + 14, "start")
        ty = y + 28
        if title:
            self.text(ax, ty, title, tsize, "bold", stroke if kind != "white" else "#1a1a1a", anc)
            ty += 24
        for i, line in enumerate(lines):
            self.text(ax, ty, line, lsize, "bold" if i in bold_lines else "normal", "#333", anc)
            ty += lsize + 6

    def chip(self, x, y, label, kind="ok"):
        fill, stroke = K[kind]
        w = 18 + 7.6 * len(label)
        self.p.append(f'<rect x="{x}" y="{y}" width="{w}" height="26" rx="13" fill="{fill}" stroke="{stroke}" stroke-width="1.4"/>')
        self.text(x + w / 2, y + 18, label, 13, color="#333", anchor="middle")
        return w

    def code(self, x, y, w, h, title, lines, title_kind="grey", size=13.5, colors=None):
        self.p.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="#F7F7F5" stroke="#C8C8C4" stroke-width="1.5"/>')
        self.text(x + 16, y + 28, title, 15.5, "bold", K[title_kind][1])
        ty = y + 56
        for i, line in enumerate(lines):
            self.text(x + 16, ty, line, size, color=(colors or {}).get(i, "#2b2b2b"), font=MONO)
            ty += size + 7

    def arrow(self, pts, label=None, lx=0, ly=0, color="#555", anchor="middle", dashed=False):
        d = "M " + " L ".join(f"{a} {b}" for a, b in pts)
        dash = ' stroke-dasharray="6 4"' if dashed else ""
        self.p.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="2"{dash} marker-end="url(#ah)"/>')
        if label:
            self.text(lx, ly, label, 13.5, color="#444", anchor=anchor, italic=True)

    def save(self, name):
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}">'
               '<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
               'orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#555"/></marker></defs>'
               f'<rect width="{self.w}" height="{self.h}" fill="#FFFFFF"/>' + "".join(self.p) + "</svg>")
        (FIG / f"{name}.svg").write_text(svg, encoding="utf-8")
        print(name, self.w, self.h)
