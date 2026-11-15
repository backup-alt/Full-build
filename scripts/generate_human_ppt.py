#!/usr/bin/env python3
"""Generate a four-slide PowerPoint about humans (human-history.pptx)."""

import os

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PPTX_PATH = os.path.join(ROOT, "human-history.pptx")

W, H = 13.333, 7.5

INK = RGBColor(0x2E, 0x2A, 0x26)
ACCENT = RGBColor(0x8B, 0x5E, 0x34)
MUTED = RGBColor(0x6B, 0x62, 0x59)
CREAM = RGBColor(0xF6, 0xF0, 0xE6)
PAPER = RGBColor(0xFF, 0xFC, 0xF7)
RULE = RGBColor(0xD8, 0xC7, 0xB2)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

FONT_HEAD = "Georgia"
FONT_BODY = "Trebuchet MS"

ERAS = [
    ("Stone Age", "c. 300,000 - 10,000 BCE",
     "Foraging bands master fire, stone tools and language, then paint the first art and invent farming."),
    ("Ancient World", "c. 3500 BCE - 500 CE",
     "Writing, cities, law codes and world religions emerge in the river valleys of Eurasia."),
    ("Middle Ages &\nEarly Modern", "500 - 1800 CE",
     "Trade, plagues and printing link continents; science and exploration remake the old order."),
    ("Revolutions &\nIndustry", "1750 - 1945 CE",
     "Steam, electricity and mass politics create modern society, along with total war."),
    ("Modern World", "1945 CE - present",
     "Computing, globalisation and biology connect eight billion people - and test the planet."),
]

TIMELINE = [
    ("300,000 BCE", "Homo sapiens appears in Africa"),
    ("70,000 BCE", "Humans disperse across Eurasia"),
    ("10,000 BCE", "Farming and settled villages begin"),
    ("3200 BCE", "Writing and the first cities"),
    ("1440 CE", "Printing press spreads knowledge"),
    ("1769 CE", "Steam power launches industry"),
    ("1969 CE", "Humans walk on the Moon"),
    ("2022 CE", "Generative AI goes mainstream"),
]

STATS = [
    ("300,000", "years as a species"),
    ("8 billion", "people alive today"),
    ("7,000+", "living languages"),
    ("12,000", "years of farming"),
]


def add_rect(slide, x, y, w, h, fill, line=None, shape=MSO_SHAPE.RECTANGLE):
    shp = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line
        shp.line.width = Pt(1)
    shp.shadow.inherit = False
    shp.text_frame.text = ""
    return shp


def add_text(slide, x, y, w, h, text, size=16, color=INK, bold=False,
             italic=False, font=FONT_BODY, align=PP_ALIGN.LEFT,
             spacing=1.0, anchor=MSO_ANCHOR.TOP, space_after=0):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    lines = text.split("\n")
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = spacing
        p.space_after = Pt(space_after)
        run = p.add_run()
        run.text = line
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.italic = italic
        run.font.name = font
        run.font.color.rgb = color
    return box


def add_rule(slide, x, y, w, color=RULE, weight=1.0):
    line = slide.shapes.add_connector(1, Inches(x), Inches(y), Inches(x + w), Inches(y))
    line.line.color.rgb = color
    line.line.width = Pt(weight)


def chrome(slide, number, label):
    add_rect(slide, 0, 0, W, H, CREAM)
    add_rect(slide, 0, 0, 0.16, H, ACCENT)
    add_text(slide, 0.85, 0.42, 8.0, 0.3, "HUMANS", size=10, color=ACCENT,
             bold=True, font=FONT_BODY)
    add_text(slide, 10.4, 0.42, 2.1, 0.3, label.upper(), size=9, color=MUTED,
             bold=True, align=PP_ALIGN.RIGHT)
    add_rule(slide, 0.85, 0.78, W - 1.7, RULE, 0.75)
    add_text(slide, 0.85, H - 0.52, 6.0, 0.28,
             "A short history of humanity", size=9, color=MUTED, italic=True)
    add_text(slide, W - 1.85, H - 0.52, 1.0, 0.28, "%d / 4" % number,
             size=9, color=MUTED, align=PP_ALIGN.RIGHT)


def slide_title(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    add_rect(s, 0, 0, W, H, INK)
    add_rect(s, 0, 0, 0.22, H, ACCENT)
    add_rect(s, 9.55, 0, 3.783, H, RGBColor(0x35, 0x30, 0x2B))

    add_text(s, 1.05, 0.95, 8.0, 0.3, "A SHORT HISTORY OF HUMANITY",
             size=12, color=RGBColor(0xC9, 0xA6, 0x7C), bold=True)
    add_rule(s, 1.05, 1.42, 2.4, ACCENT, 2.0)
    add_text(s, 1.0, 1.85, 8.2, 1.7, "Humans", size=92, color=PAPER,
             bold=True, font=FONT_HEAD)
    add_text(s, 1.05, 3.55, 7.6, 0.9,
             "From the first footsteps in Africa to a networked\nplanet of eight billion people.",
             size=20, color=RGBColor(0xE4, 0xD6, 0xC4), spacing=1.15)

    stats = [("300,000 yrs", "as a species"), ("8 billion", "alive today"),
             ("5 eras", "of shared history")]
    x = 1.05
    for value, label in stats:
        add_text(s, x, 5.25, 2.35, 0.4, value, size=22, color=PAPER,
                 bold=True, font=FONT_HEAD)
        add_text(s, x, 5.72, 2.35, 0.3, label, size=11, color=RGBColor(0xB7, 0xA8, 0x95))
        x += 2.55

    add_text(s, 1.05, 6.55, 7.0, 0.3,
             "Four slides  |  c. 300,000 BCE to the present", size=11,
             color=RGBColor(0x9B, 0x8B, 0x77))

    add_text(s, 10.35, 0.95, 2.25, 0.35, "AT A GLANCE", size=10,
             color=RGBColor(0xC9, 0xA6, 0x7C), bold=True)
    add_rule(s, 10.35, 1.35, 2.15, RGBColor(0x5C, 0x53, 0x4A), 0.75)
    facts = [
        ("98.8%", "of our history was\nlived as foragers"),
        ("c. 10,000 BCE", "farming begins"),
        ("1450s", "knowledge becomes\nmass-produced"),
        ("1969", "humans leave\nthe planet"),
        ("2022", "machine intelligence\narrives"),
    ]
    y = 1.7
    for value, label in facts:
        add_text(s, 10.35, y, 2.3, 0.3, value, size=15, color=PAPER,
                 bold=True, font=FONT_HEAD)
        add_text(s, 10.35, y + 0.3, 2.3, 0.6, label, size=10,
                 color=RGBColor(0xB7, 0xA8, 0x95), spacing=1.05)
        y += 0.98
    return s


def slide_origins(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    chrome(s, 2, "Origins")
    add_text(s, 0.85, 1.05, 10.5, 0.7, "We are one species with one origin",
             size=34, color=INK, bold=True, font=FONT_HEAD)
    add_text(s, 0.85, 1.78, 9.2, 0.65,
             "Homo sapiens evolved in Africa around 300,000 years ago. Language, "
             "cooperation and tool-making let a fragile primate spread to every continent.",
             size=15, color=MUTED, spacing=1.15)

    cards = [
        ("01", "Origins", "Fossils from Jebel Irhoud and Omo Kibish place our earliest "
                          "ancestors in Africa. Small bands hunted, gathered and buried "
                          "their dead with care."),
        ("02", "Dispersal", "A major migration about 70,000 years ago reached Australia, "
                            "Europe and the Americas. Humans adapted to deserts, jungles "
                            "and ice ages."),
        ("03", "Symbols", "Cave paintings, carved figurines and music appear by 45,000 BCE - "
                          "evidence that imagination, ritual and storytelling are ancient."),
        ("04", "Farming", "Around 10,000 BCE people began cultivating crops and herding "
                          "animals. Surplus food led to villages, property, cities and "
                          "recorded history."),
    ]
    x = 0.85
    for num, head, body in cards:
        add_rect(s, x, 2.72, 2.83, 3.45, PAPER, RULE)
        add_text(s, x + 0.28, 2.92, 1.0, 0.35, num, size=11, color=ACCENT, bold=True)
        add_text(s, x + 0.28, 3.3, 2.3, 0.45, head, size=20, color=INK,
                 bold=True, font=FONT_HEAD)
        add_rule(s, x + 0.28, 3.82, 2.0, RULE, 0.75)
        add_text(s, x + 0.28, 3.98, 2.28, 1.95, body, size=12, color=MUTED, spacing=1.18)
        x += 3.05

    add_rect(s, 0.85, 6.42, 11.65, 0.52, INK)
    add_text(s, 1.1, 6.53, 11.2, 0.32,
             "KEY IDEA   Humans survived not by strength but by sharing knowledge across generations.",
             size=12, color=PAPER, bold=True)
    return s


def slide_eras(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    chrome(s, 3, "Five eras")
    add_text(s, 0.85, 1.05, 10.0, 0.7, "From villages to a global civilisation",
             size=34, color=INK, bold=True, font=FONT_HEAD)

    add_rule(s, 0.95, 2.55, 11.4, RULE, 1.25)
    x = 0.85
    for i, (name, span, desc) in enumerate(ERAS):
        add_rect(s, x + 0.55, 2.45, 0.2, 0.2, ACCENT, shape=MSO_SHAPE.OVAL)
        add_text(s, x, 2.78, 2.2, 0.32, span, size=10, color=ACCENT, bold=True)
        add_text(s, x, 3.12, 2.2, 0.85, name, size=17, color=INK,
                 bold=True, font=FONT_HEAD, spacing=0.95)
        add_text(s, x, 4.02, 2.15, 2.0, desc, size=11, color=MUTED, spacing=1.16)
        if i < len(ERAS) - 1:
            line = s.shapes.add_connector(1, Inches(x + 2.24), Inches(3.05),
                                          Inches(x + 2.24), Inches(5.85))
            line.line.color.rgb = RULE
            line.line.width = Pt(0.75)
        x += 2.38

    add_rect(s, 0.85, 6.3, 11.65, 0.7, PAPER, RULE)
    add_text(s, 1.1, 6.42, 11.1, 0.48,
             "Each era built on the last: farming fed cities, cities needed writing, writing "
             "carried science, and science created industry.",
             size=12, color=MUTED, italic=True)
    return s


def slide_modern(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    chrome(s, 4, "Now & next")
    add_text(s, 0.85, 1.05, 11.0, 0.7, "The modern human",
             size=34, color=INK, bold=True, font=FONT_HEAD)
    add_text(s, 0.85, 1.76, 6.4, 0.85,
             "We live longer, travel farther and know more than any generation before us. "
             "The same tools that lifted billions out of poverty now test the planet.",
             size=14, color=MUTED, spacing=1.18)

    add_text(s, 0.85, 2.9, 2.2, 0.3, "MILESTONES", size=10, color=ACCENT, bold=True)
    add_rule(s, 0.85, 3.22, 5.9, RULE, 0.75)
    y = 3.38
    for i, (date, label) in enumerate(TIMELINE):
        add_text(s, 0.85, y, 1.35, 0.26, date, size=10, color=ACCENT, bold=True)
        add_text(s, 2.28, y, 4.45, 0.26, label, size=12, color=INK)
        if i < len(TIMELINE) - 1:
            add_rule(s, 0.85, y + 0.33, 5.88, RULE, 0.4)
        y += 0.36

    add_rect(s, 6.85, 1.72, 5.65, 4.35, INK)
    add_text(s, 7.25, 1.98, 4.9, 0.3, "THE NEXT CHAPTER", size=10,
             color=RGBColor(0xC9, 0xA6, 0x7C), bold=True)
    add_text(s, 7.25, 2.35, 4.9, 0.5, "Shared problems,\nshared tools",
             size=24, color=PAPER, bold=True, font=FONT_HEAD, spacing=1.0)
    add_rule(s, 7.25, 3.42, 4.8, RGBColor(0x5C, 0x53, 0x4A), 0.75)

    challenges = [
        ("Climate", "Emissions and heat reshape where and how we can live."),
        ("Inequality", "Wealth and opportunity remain unevenly shared."),
        ("Intelligence", "AI extends human capability - and raises hard questions."),
    ]
    y = 3.6
    for head, body in challenges:
        add_text(s, 7.25, y, 1.75, 0.28, head, size=12, color=PAPER, bold=True)
        add_text(s, 9.02, y, 3.1, 0.7, body, size=10.5,
                 color=RGBColor(0xC9, 0xBD, 0xAD), spacing=1.1)
        y += 0.78

    x = 0.85
    for value, label in STATS:
        add_text(s, x, 6.26, 2.4, 0.34, value, size=20, color=ACCENT,
                 bold=True, font=FONT_HEAD)
        add_text(s, x, 6.62, 2.4, 0.26, label, size=10, color=MUTED)
        x += 2.9
    return s


def build():
    prs = Presentation()
    prs.slide_width = Inches(W)
    prs.slide_height = Inches(H)
    prs.core_properties.title = "Humans: A Short History"
    prs.core_properties.subject = "A four-slide overview of human history"
    prs.core_properties.author = "Full-build"

    slide_title(prs)
    slide_origins(prs)
    slide_eras(prs)
    slide_modern(prs)

    prs.save(PPTX_PATH)
    return PPTX_PATH


if __name__ == "__main__":
    path = build()
    print(path, os.path.getsize(path), "bytes,", len(Presentation(path).slides), "slides")
