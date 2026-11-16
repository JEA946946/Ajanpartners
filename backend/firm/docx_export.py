"""Flettet Markdown → Word (.docx): overskrifter, afsnit, **fed**, punkter, afkrydsning, tabeller og citater."""

import io
import re

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

_INLINE = re.compile(r"(\*\*[^*]+\*\*|\*[^*\s][^*]*\*)")


def _runs(par, text):
    for part in _INLINE.split(text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            par.add_run(part[2:-2]).bold = True
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            par.add_run(part[1:-1]).italic = True
        else:
            par.add_run(part)


def _shade(cell, color="EDEDED"):
    tc = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:fill"), color)
    tc.append(shd)


def markdown_to_docx(text, title="", firm_name=""):
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(10.5)
    if firm_name:
        hp = doc.sections[0].header.paragraphs[0]
        hp.text = firm_name
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hp.runs[0].font.size = Pt(9)
        hp.runs[0].font.color.rgb = RGBColor(0x66, 0x66, 0x66)
    doc.core_properties.title = title

    lines = text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        if line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
                    rows.append(cells)
                i += 1
            if rows:
                width = max(len(r) for r in rows)
                table = doc.add_table(rows=len(rows), cols=width)
                table.style = "Table Grid"
                for r, row in enumerate(rows):
                    for c in range(width):
                        cell = table.cell(r, c)
                        cell.text = ""
                        _runs(cell.paragraphs[0], row[c] if c < len(row) else "")
                        if r == 0:
                            for run in cell.paragraphs[0].runs:
                                run.bold = True
                            _shade(cell)
                doc.add_paragraph()
            continue
        m = re.match(r"^(#{1,4})\s+(.*)", line)
        if m:
            doc.add_heading(m.group(2), level=min(len(m.group(1)), 4))
        elif re.match(r"^\s*- \[( |x|X)\] ", line):
            checked = re.match(r"^\s*- \[(x|X)\]", line) is not None
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Pt(14 if line.startswith(" ") else 0)
            _runs(p, ("☒ " if checked else "☐ ") + re.sub(r"^\s*- \[.\] ", "", line))
        elif re.match(r"^\s*[-*] ", line):
            p = doc.add_paragraph(style="List Bullet 2" if line.startswith("  ") else "List Bullet")
            _runs(p, re.sub(r"^\s*[-*] ", "", line))
        elif re.match(r"^\s*\d+[.)] ", line):
            p = doc.add_paragraph(style="List Number")
            _runs(p, re.sub(r"^\s*\d+[.)] ", "", line))
        elif line.startswith(">"):
            p = doc.add_paragraph(style="Intense Quote")
            _runs(p, line.lstrip("> "))
        elif re.fullmatch(r"-{3,}|_{3,}|\*{3,}", line.strip()):
            doc.add_paragraph("_" * 60)
        elif line.strip():
            p = doc.add_paragraph()
            _runs(p, line)
        i += 1
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()
