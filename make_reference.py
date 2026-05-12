"""
Creates a custom reference.docx for pandoc with clean, Markdown-like styling.
"""
import os
os.chdir('/home/user/audio')

from docx import Document
from docx.shared import Pt, RGBColor, Cm

doc = Document('reference.docx')

def get_style(name_id, type_id=1):
    return doc.styles.get_by_id(name_id, type_id)

def set_style(style, font_name='Calibri', font_size=11, bold=False, italic=False,
              color=None, space_before=0, space_after=6, keep_with_next=False,
              left_indent=None, line_spacing=None):
    f = style.font
    f.name = font_name
    f.size = Pt(font_size)
    f.bold = bold
    f.italic = italic
    if color:
        f.color.rgb = RGBColor(*color)
    pf = style.paragraph_format
    pf.space_before = Pt(space_before)
    pf.space_after = Pt(space_after)
    if keep_with_next:
        pf.keep_with_next = True
    if left_indent is not None:
        pf.left_indent = left_indent
    if line_spacing is not None:
        pf.line_spacing = line_spacing

DARK_BLUE  = (31,  73,  125)
MED_BLUE   = (68, 114,  196)
DARK_GRAY  = (64,  64,   64)
BLACK      = (0,    0,    0)
RED_DARK   = (192,  0,    0)

# ── Heading 1: section headers (OTOLOGIE, RHINOLOGIE etc.)
h1 = get_style('Heading1')
set_style(h1, font_size=18, bold=True, color=DARK_BLUE,
          space_before=20, space_after=6, keep_with_next=True)
h1.font.all_caps = True

# ── Heading 2: guideline titles (## 1. Audiologische zorg...)
h2 = get_style('Heading2')
set_style(h2, font_size=14, bold=True, color=DARK_BLUE,
          space_before=14, space_after=4, keep_with_next=True)

# ── Heading 3: module headers (### Module 1 — Definitie)
h3 = get_style('Heading3')
set_style(h3, font_size=11, bold=True, color=MED_BLUE,
          space_before=10, space_after=3, keep_with_next=True)

# ── Heading 4: sub-sections
h4 = get_style('Heading4')
set_style(h4, font_size=10, bold=True, italic=True, color=DARK_GRAY,
          space_before=8, space_after=2, keep_with_next=True)

# ── Normal body text
normal = get_style('Normal')
set_style(normal, font_size=10, color=BLACK,
          space_before=0, space_after=4, line_spacing=Pt(13))

# ── Body Text
bt = get_style('BodyText')
set_style(bt, font_size=10, space_before=0, space_after=4)

# ── Compact (used for tight lists/paragraphs by pandoc)
try:
    compact = get_style('Compact')
    set_style(compact, font_size=10, space_before=0, space_after=2)
except Exception:
    pass

# ── List Bullet styles
for style_id, indent in [('ListBullet', Cm(0.5)), ('ListBullet2', Cm(1.0)),
                          ('ListBullet3', Cm(1.5))]:
    try:
        s = get_style(style_id)
        set_style(s, font_size=10, space_before=0, space_after=2,
                  left_indent=indent)
    except Exception:
        pass

# ── Verbatim (code blocks)
try:
    v = get_style('VerbatimChar', type_id=2)
    v.font.name = 'Courier New'
    v.font.size = Pt(9)
except Exception:
    pass

# ── Page margins (A4)
section = doc.sections[0]
section.left_margin   = Cm(2.5)
section.right_margin  = Cm(2.5)
section.top_margin    = Cm(2.5)
section.bottom_margin = Cm(2.5)

doc.save('reference_custom.docx')
print("Saved reference_custom.docx")
