"""Export the README proposal body to standalone Markdown and an A4 PDF.

The repository guide is excluded from the proposal. Contents are read directly
from README.md; this script does not maintain a second manuscript.
"""

from __future__ import annotations

import html
import hashlib
import json
import re
from pathlib import Path

from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph,
                               SimpleDocTemplate, Spacer, Table, TableStyle)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "pdf"


def inline(value: str) -> str:
    value = html.escape(value)
    value = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", value)
    value = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", value)
    value = re.sub(r"`([^`]+)`", r"<font name='Courier'>\1</font>", value)
    value = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", value)
    return value


def build() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "proposal.pdf"
    source = (ROOT / "README.md").read_text(encoding="utf-8-sig")
    source = source.split("## Repository guide")[0].strip()
    (ROOT / "PROPOSAL.md").write_text(source + "\n", encoding="utf-8")
    body = ParagraphStyle("Body", fontName="Helvetica", fontSize=10,
                          leading=12.2, spaceAfter=5, textColor=colors.HexColor("#16232c"))
    heading = ParagraphStyle("Heading", parent=body, fontName="Helvetica-Bold",
                             fontSize=11.3, leading=13.4, spaceBefore=8, spaceAfter=5,
                             keepWithNext=True, textColor=colors.HexColor("#163e56"))
    title = ParagraphStyle("Title", parent=heading, fontSize=17.5, leading=21,
                           spaceBefore=0, spaceAfter=8)
    bullet = ParagraphStyle("Bullet", parent=body, leftIndent=9, firstLineIndent=-7)
    cell_style = ParagraphStyle("Cell", parent=body, fontSize=8.8, leading=10.2, spaceAfter=0)
    caption = ParagraphStyle("Caption", parent=body, fontSize=8.2, leading=10, spaceAfter=5)
    refs = ParagraphStyle("Reference", parent=body, fontSize=10, leading=12.5, spaceAfter=10)
    doc = SimpleDocTemplate(str(path), pagesize=A4, leftMargin=42, rightMargin=42,
                            topMargin=36, bottomMargin=36, title="Agulhas transport proposal",
                            author="DATA3001 Group 2")
    width = A4[0] - 84
    story = []
    lines = source.splitlines()
    in_references = False
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line == "## References":
            story.extend([PageBreak(), Paragraph("References", heading)])
            in_references = True
        elif line.startswith("# "):
            story.append(Paragraph(inline(line[2:]), title))
        elif line.startswith("## "):
            story.append(Paragraph(inline(line[3:]), heading))
        elif line.startswith("!["):
            target = re.search(r"\]\(([^)]+)\)", line).group(1)
            image_path = ROOT / target
            from PIL import Image as PILImage
            iw, ih = PILImage.open(image_path).size
            draw_width = 300
            picture = Image(str(image_path), draw_width, draw_width * ih / iw)
            picture.hAlign = "CENTER"
            items = [picture, Spacer(1, 3)]
            if i + 2 < len(lines) and lines[i + 2].strip().startswith("*Figure"):
                items.append(Paragraph(inline(lines[i + 2]), caption))
                i += 2
            story.append(KeepTogether(items))
        elif line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                vals = [v.strip() for v in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-+:?", v) for v in vals):
                    rows.append([Paragraph(inline(v), cell_style) for v in vals])
                i += 1
            i -= 1
            if len(rows[0]) == 5:
                cols = [width * x for x in [0.30, 0.15, 0.15, 0.22, 0.18]]
            elif len(rows[0]) == 2:
                cols = [width * x for x in [0.22, 0.78]]
            elif rows[0][1].getPlainText() == "Student ID":
                cols = [width * x for x in [0.25, 0.20, 0.55]]
            else:
                cols = [width * x for x in [0.24, 0.51, 0.25]]
            table = Table(rows, colWidths=cols, repeatRows=1, hAlign="LEFT")
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e6eff5")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LINEBELOW", (0, 0), (-1, 0), .6, colors.HexColor("#6d899e")),
                ("LINEBELOW", (0, 1), (-1, -1), .3, colors.HexColor("#cbd6dd")),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.extend([table, Spacer(1, 5)])
        elif line.startswith("- "):
            story.append(Paragraph(inline(line[2:]), refs if in_references else bullet,
                                   bulletText=None if in_references else "-"))
        else:
            story.append(Paragraph(inline(line), refs if in_references else body))
        i += 1

    def footer(canvas, document):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#ccd7df"))
        canvas.line(42, 27, A4[0] - 42, 27)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#52616d"))
        canvas.drawString(42, 15, "DATA3001 | Group 2 | Project proposal")
        canvas.drawRightString(A4[0] - 42, 15, str(document.page))
        canvas.restoreState()

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    reader = PdfReader(path)
    pages = [p.extract_text() or "" for p in reader.pages]
    ref_pages = [i for i, text in enumerate(pages) if re.search(r"(?m)^References\s*$", text)]
    if len(ref_pages) != 1:
        raise ValueError("Cannot determine where references start")
    body_pages = ref_pages[0]
    full_text = "\n".join(pages)
    for number, name in enumerate(["Research questions and objectives", "Data/region and data description",
                                   "Why this problem is important", "Background and existing studies",
                                   "Proposed method"], 1):
        if f"{number}. {name}" not in full_text:
            raise ValueError(f"Missing proposal section {number}")
    summary = {"body_pages": body_pages, "reference_pages": len(pages) - body_pages,
               "page_size": "A4", "source": "README.md", "repository_guide_excluded": True,
               "markdown_output": "PROPOSAL.md",
               "readme_sha256": hashlib.sha256((ROOT / "README.md").read_bytes()).hexdigest(),
               "proposal_source_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
               "markdown_sha256": hashlib.sha256((ROOT / "PROPOSAL.md").read_bytes()).hexdigest(),
               "pdf_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
               "named_team_allocation": "omitted from proposal at user request; TEAM_ALLOCATION.md retained separately",
               "visual_review": "pending"}
    (OUT / "layout_check.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary))
    if body_pages > 3:
        raise ValueError(f"Body occupies {body_pages} pages, exceeding the three-page limit")


if __name__ == "__main__":
    build()
