#!/usr/bin/env python3
"""Generate the 5-page human history PDF, Word document and Excel workbook."""

import os
from datetime import date

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, Table,
    TableStyle, PageBreak, KeepTogether,
)

import openpyxl
from openpyxl.chart import LineChart, Reference
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF_PATH = os.path.join(ROOT, "human-history.pdf")
DOCX_PATH = os.path.join(ROOT, "human-history.docx")
XLSX_PATH = os.path.join(ROOT, "human-history.xlsx")

INK = colors.HexColor("#2E2A26")
ACCENT = colors.HexColor("#8B5E34")
MUTED = colors.HexColor("#6B6259")
LIGHT = colors.HexColor("#F3ECE1")
RULE = colors.HexColor("#D8C7B2")

TITLE = "A Concise History of Humanity"
SUBTITLE = "From the first humans to the age of artificial intelligence"


class Era:
    def __init__(self, number, name, span, lede, sections, events, legacy):
        self.number = number
        self.name = name
        self.span = span
        self.lede = lede
        self.sections = sections      # list of (heading, body)
        self.events = events          # list of (date, event, significance)
        self.legacy = legacy


ERAS = [
    Era(
        1,
        "Prehistory and the Stone Age",
        "c. 300,000 BCE - 10,000 BCE",
        "Human history begins in Africa. Over roughly 290,000 years our species spread "
        "across the planet, mastered fire and stone, built the first symbolic cultures, "
        "and - at the very end of the period - invented farming. With no written records, "
        "it is reconstructed from fossils, genetics and archaeology.",
        [
            ("Origins and dispersal",
             "Homo sapiens emerged in Africa around 300,000 years ago. The oldest fossils come "
             "from Jebel Irhoud in Morocco (about 315,000 years ago) and Omo Kibish in "
             "Ethiopia (about 230,000 years ago). Groups "
             "left Africa in several waves; the successful dispersal about 70,000 years ago "
             "reached Australia by 50,000 BCE, Europe by 45,000 BCE and the Americas by "
             "15,000 BCE."),
            ("Tools, fire and language",
             "Stone tools, controlled fire, tailored clothing and composite weapons let "
             "humans occupy cold Eurasia. Complex language and cooperative hunting were "
             "decisive advantages over other hominins such as Neanderthals, who disappeared "
             "about 40,000 years ago. By 40,000 BCE people were painting animals in caves "
             "in Sulawesi, Chauvet and Lascaux, carving figurines and burying their dead "
             "with ornaments - the earliest evidence of religion and art."),
            ("The Neolithic Revolution",
             "Around 10,000 BCE communities in the Fertile Crescent began cultivating wheat, "
             "barley and legumes and herding sheep and goats. Farming appeared independently "
             "in China (rice, millet), Mesoamerica (maize), New Guinea and West Africa. "
             "Settled villages, surplus food, pottery and eventually metalworking followed, "
             "setting the material foundations for cities and writing."),
        ],
        [
            ("c. 300,000 BCE", "First Homo sapiens", "Our species appears in Africa"),
            ("c. 70,000 BCE", "Out of Africa dispersal", "Humans settle across Eurasia"),
            ("c. 45,000 BCE", "Cave art and music", "Symbolic culture flourishes"),
            ("c. 10,000 BCE", "Agriculture begins", "Farming and villages emerge"),
            ("c. 3500 BCE", "First cities and writing", "History becomes recorded"),
        ],
        legacy="The Stone Age left humanity its languages, kinship systems, art and detailed knowledge of the natural world. Farming then created the surplus that made cities, property and states possible.",
    ),
    Era(
        2,
        "The Ancient World",
        "c. 3500 BCE - 500 CE",
        "The invention of writing around 3200 BCE marks the start of recorded history. "
        "River valleys in Mesopotamia, Egypt, the Indus and China produced the first states, "
        "laws, monumental architecture and world religions. The era ends with the collapse "
        "of the Western Roman Empire and the transformation of the classical world.",
        [
            ("The first civilisations",
             "Sumerian city-states such as Uruk developed cuneiform writing, the wheel, "
             "irrigation and the first law codes. Egypt unified around 3000 BCE and built the "
             "pyramids at Giza a few centuries later. The Indus Valley cities of Harappa and "
             "Mohenjo-daro had planned streets and drainage by 2600 BCE, while the Shang "
             "dynasty ruled northern China from about 1600 BCE, leaving oracle-bone script."),
            ("Empires and the Axial Age",
             "Between 800 and 200 BCE - the Axial Age - Confucius, the Buddha, the Hebrew "
             "prophets and Greek philosophers reshaped how humans understood ethics, politics "
             "and the cosmos. Persia's Achaemenid Empire, Alexander the Great's conquests "
             "(336-323 BCE), the Mauryan Empire in India and the Qin unification of China "
             "(221 BCE) created vast, connected realms linked by roads and trade."),
            ("Greece, Rome and late antiquity",
             "Athenian democracy (508 BCE) and Greek science and drama shaped later European "
             "thought. Rome grew from a republic into an empire ruling the Mediterranean from "
             "27 BCE, spreading Latin law, roads and citizenship. Christianity emerged in "
             "Judaea and became Rome's state religion in 380 CE. In 476 CE the last western "
             "emperor was deposed, while the eastern Roman (Byzantine) Empire endured for "
             "another thousand years."),
        ],
        [
            ("c. 3200 BCE", "Cuneiform writing", "Recorded history begins in Sumer"),
            ("c. 2560 BCE", "Great Pyramid of Giza", "Peak of Egyptian engineering"),
            ("c. 1200 BCE", "Bronze Age collapse", "Trade networks fracture"),
            ("508 BCE", "Athenian democracy", "Citizens share political power"),
            ("221 BCE", "Qin unifies China", "Imperial China takes shape"),
            ("27 BCE", "Roman Empire founded", "Augustus becomes first emperor"),
            ("476 CE", "Fall of Western Rome", "Classical antiquity ends"),
        ],
        legacy="The ancient world gave us the alphabet, coinage, written law, monotheism, philosophy and the idea of citizenship - institutions still recognisable today.",
    ),
    Era(
        3,
        "The Middle Ages and Early Modern World",
        "500 CE - 1800 CE",
        "After Rome's fall, new religions and empires knitted Eurasia together. Islamic "
        "scholarship, Chinese invention and European feudalism coexisted with the Mongol "
        "conquests and the Black Death. Printing, global navigation and the Reformation then "
        "broke Europe's medieval order and opened an age of worldwide exchange.",
        [
            ("Faiths, empires and exchange",
             "Islam spread from Arabia after 622 CE across the Middle East, North Africa and "
             "Spain; Baghdad's House of Wisdom preserved and extended Greek science. Tang and "
             "Song China produced gunpowder, paper money and printing, while the Byzantine "
             "Empire and Charlemagne's coronation (800) framed European politics. The Silk "
             "Road carried goods, ideas and disease between Asia, Africa and Europe."),
            ("Plague, conquest and recovery",
             "Genghis Khan united the Mongols in 1206 and built the largest contiguous land "
             "empire in history, reopening transcontinental trade. The Black Death killed "
             "perhaps a third of Europe's people after 1347, weakening serfdom and the "
             "Church. In its wake came the Renaissance in Italy, the fall of Constantinople "
             "(1453), and the printing press of Johannes Gutenberg (c. 1440), which "
             "democratised knowledge."),
            ("Discovery and enlightenment",
             "Columbus crossed the Atlantic in 1492, beginning the Columbian Exchange of "
             "crops, animals, people and diseases. Portugal and Spain built global empires, "
             "followed by the Dutch, French and British. The Reformation (1517) shattered "
             "religious unity; the Scientific Revolution placed observation above authority; "
             "and Enlightenment thinkers championed reason, rights and progress. By 1800 the "
             "world was linked by trade, but also by slavery and colonial rivalry."),
        ],
        [
            ("622", "Hijra of Muhammad", "Islamic calendar begins"),
            ("800", "Charlemagne crowned", "Medieval Europe consolidated"),
            ("1206", "Mongol Empire founded", "Eurasia politically connected"),
            ("1347", "Black Death reaches Europe", "Demographic catastrophe"),
            ("c. 1440", "Gutenberg's printing press", "Knowledge mass-produced"),
            ("1492", "Columbus reaches the Americas", "Global exchange begins"),
            ("1543", "Copernicus's heliocentric model", "Scientific Revolution starts"),
            ("1687", "Newton's Principia", "Physics mathematised"),
        ],
        legacy="Early modern Europe exported the sovereign state, global trade, printed knowledge and science as a shared method of inquiry, while the Columbian Exchange permanently reshaped diets and populations on every continent.",
    ),
    Era(
        4,
        "Revolutions and Industry",
        "1750 CE - 1945 CE",
        "In under two centuries, steam, steel, electricity and the internal combustion "
        "engine remade daily life. Political revolutions spread the ideas of liberty and "
        "nationality, while industrial empires and total war produced both unprecedented "
        "prosperity and unprecedented destruction.",
        [
            ("Industrial Revolution",
             "Britain's coal, iron and cotton industries, powered by James Watt's improved "
             "steam engine (1769), launched sustained economic growth. Railways, steamships, "
             "telegraphs and later electricity and chemicals compressed distance and time. "
             "Urbanisation, factory labour and a new working class followed, along with "
             "trade unions, public schooling and mass politics."),
            ("Political upheaval",
             "The American Declaration of Independence (1776) and the French Revolution "
             "(1789) asserted popular sovereignty and equal rights. Napoleon's wars spread "
             "and then discredited revolutionary ideals, but nationalism and liberalism "
             "survived. Latin America won independence, Germany and Italy unified, and the "
             "United States abolished slavery after the Civil War (1861-65). Marxism and "
             "democratic socialism offered rival answers to industrial inequality."),
            ("Empire, science and total war",
             "European powers partitioned Africa and contested Asia, while Japan's Meiji "
             "Restoration (1868) created a new imperial power. Darwin's theory of evolution, "
             "germ theory, relativity and psychoanalysis transformed knowledge. World War I "
             "(1914-18) killed some 17 million people; the 1929 Depression, fascism and "
             "Stalinism led to World War II (1939-45), the Holocaust and the atomic bomb, "
             "ending Europe's global primacy."),
        ],
        [
            ("1769", "Watt's steam engine", "Industrial power harnessed"),
            ("1776", "US Declaration of Independence", "Rights-based republic founded"),
            ("1789", "French Revolution", "Monarchy and privilege challenged"),
            ("1859", "Darwin's Origin of Species", "Evolution explains life"),
            ("1914-18", "World War I", "Industrialised mass warfare"),
            ("1929", "Great Depression", "Global economy collapses"),
            ("1939-45", "World War II", "Total war and the atomic age"),
        ],
        legacy="Industrial society produced mass production, mass politics and the welfare state - and, after 1945, a body of human-rights law born from the catastrophes of total war.",
    ),
    Era(
        5,
        "The Modern World",
        "1945 CE - present",
        "The post-war order was built on the United Nations, human rights and competing "
        "superpowers. Decolonisation created more than a hundred new states, while computing, "
        "globalisation and biotechnology transformed economies and societies. Humanity now "
        "faces shared challenges that no single nation can solve alone.",
        [
            ("Cold War and decolonisation",
             "The United States and the Soviet Union divided the world into rival blocs, "
             "racing for nuclear weapons and influence from Korea to Cuba and Vietnam. India "
             "and Pakistan gained independence in 1947, followed by most of Africa and Asia "
             "by the 1960s. The Berlin Wall fell in 1989 and the USSR dissolved in 1991, "
             "ending the Cold War but not great-power rivalry."),
            ("Science, technology and globalisation",
             "Sputnik (1957) and the Moon landing (1969) opened the space age. Vaccines "
             "eradicated smallpox; the Green Revolution fed billions. The transistor, the "
             "personal computer, the internet and the smartphone created a networked global "
             "economy. Trade liberalisation lifted hundreds of millions out of poverty, even "
             "as inequality and financial crises (2008) exposed its fragilities."),
            ("The present and its challenges",
             "World population passed eight billion in 2022 after growing from 2.5 billion "
             "in 1950. The COVID-19 pandemic (2020-23) tested health systems and accelerated "
             "remote work and digital services. Climate change, migration, pandemics, "
             "disinformation and the rapid rise of artificial intelligence since 2022 define "
             "the current era - a moment in which humanity's tools are again reshaping what "
             "it means to be human."),
        ],
        [
            ("1945", "United Nations founded", "Rules-based world order"),
            ("1947", "India independent; Cold War", "Decolonisation accelerates"),
            ("1957 / 1969", "Sputnik / Moon landing", "Space age begins"),
            ("1989-91", "Berlin Wall falls; USSR ends", "Cold War concludes"),
            ("1991", "World Wide Web goes public", "Information age begins"),
            ("2020-23", "COVID-19 pandemic", "Global systems stress-tested"),
            ("2022-", "Generative AI boom", "Machine intelligence spreads"),
        ],
        legacy="The modern world has made information, travel and medicine ordinary - and turned climate change, inequality and artificial intelligence into shared, global problems.",
    ),
]


STATS = {
    1: [("300,000 yrs", "Span of the Stone Age"),
        ("4 million", "World population, 10,000 BCE"),
        ("45,000 BCE", "Earliest figurative art")],
    2: [("3,200 BCE", "Writing invented"),
        ("1 million", "Peak population of Rome"),
        ("4,000 yrs", "Length of the era")],
    3: [("200 million", "Estimated Black Death deaths"),
        ("8+ million", "Books printed by 1500"),
        ("1,300 yrs", "Length of the era")],
    4: [("17 million", "Deaths in World War I"),
        ("70-85 million", "Deaths in World War II"),
        ("195 yrs", "Length of the era")],
}


INTRO = (
    "This document condenses roughly 300,000 years of human history into five eras: the "
    "(1) Stone Age, (2) ancient world, (3) Middle Ages and early modern world, (4) age of "
    "revolutions and industry, and (5) modern world since 1945. Dates are approximate and "
    "use BCE (Before Common Era) or CE (Common Era)."
)

CLOSING = (
    "History is not a single story. Trade, migration, disease, ideas and technology have "
    "always connected societies, and ordinary people have shaped every era as much as rulers "
    "and inventions. The same record that produced agriculture, writing, science and human "
    "rights also produced slavery, war and ecological strain. Understanding that double "
    "inheritance is the practical value of history: it widens our sense of what is possible "
    "and what is at stake in the present."
)

SOURCES = [
    "McNeill, J. R. & McNeill, W. H., The Human Web: A Bird's-Eye View of World History (2003).",
    "Harari, Y. N., Sapiens: A Brief History of Humankind (2011).",
    "Roberts, J. M., The New Penguin History of the World, 5th ed. (2007).",
    "Christian, D., Maps of Time: An Introduction to Big History (2004).",
    "United Nations, World Population Prospects (2022 revision).",
    "Smithsonian National Museum of Natural History, 'Human Origins' (2023).",
]


# --------------------------------------------------------------------------- PDF
def build_pdf():
    styles = getSampleStyleSheet()
    body = ParagraphStyle(
        "Body", parent=styles["BodyText"], fontName="Helvetica", fontSize=9.65,
        leading=13.75, textColor=INK, alignment=TA_JUSTIFY, spaceAfter=5,
    )
    lede = ParagraphStyle(
        "Lede", parent=body, fontSize=10.2, leading=14.2, textColor=MUTED,
        fontName="Helvetica-Oblique", spaceAfter=9,
    )
    h1 = ParagraphStyle(
        "H1", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=20,
        leading=23, textColor=INK, spaceAfter=2,
    )
    h2 = ParagraphStyle(
        "H2", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=12.5,
        leading=15, textColor=ACCENT, spaceBefore=8, spaceAfter=3,
    )
    h3 = ParagraphStyle(
        "H3", parent=styles["Heading3"], fontName="Helvetica-Bold", fontSize=9.6,
        leading=12, textColor=INK, spaceBefore=5, spaceAfter=1.5,
    )
    kicker = ParagraphStyle(
        "Kicker", parent=body, fontName="Helvetica-Bold", fontSize=8,
        textColor=ACCENT, alignment=TA_LEFT, spaceAfter=3,
    )
    caption = ParagraphStyle(
        "Caption", parent=body, fontName="Helvetica-Oblique", fontSize=8,
        textColor=MUTED, alignment=TA_LEFT, spaceAfter=0,
    )

    def header_footer(canv, doc):
        canv.saveState()
        w, h = letter
        if doc.page > 1:
            canv.setFont("Helvetica", 7.6)
            canv.setFillColor(MUTED)
            canv.drawString(1.9 * cm, h - 1.35 * cm, TITLE.upper())
            if doc.page <= len(ERAS):
                canv.drawRightString(w - 1.9 * cm, h - 1.35 * cm, ERAS[doc.page - 1].span)
            canv.setStrokeColor(RULE)
            canv.setLineWidth(0.6)
            canv.line(1.9 * cm, h - 1.5 * cm, w - 1.9 * cm, h - 1.5 * cm)
        canv.setStrokeColor(RULE)
        canv.setLineWidth(0.6)
        canv.line(1.9 * cm, 1.65 * cm, w - 1.9 * cm, 1.65 * cm)
        canv.setFont("Helvetica", 7.6)
        canv.setFillColor(MUTED)
        canv.drawString(1.9 * cm, 1.15 * cm, "Generated %s" % date.today().isoformat())
        canv.drawRightString(w - 1.9 * cm, 1.15 * cm, "Page %d of 5" % doc.page)
        canv.restoreState()

    doc = BaseDocTemplate(
        PDF_PATH, pagesize=letter,
        leftMargin=1.9 * cm, rightMargin=1.9 * cm,
        topMargin=1.9 * cm, bottomMargin=1.9 * cm,
        title=TITLE, author="Full-build", subject="A five-page history of humanity",
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="main")
    doc.addPageTemplates([PageTemplate(id="page", frames=[frame], onPage=header_footer)])

    story = []
    for i, era in enumerate(ERAS):
        if i == 0:
            story.append(Paragraph("HUMAN HISTORY IN FIVE ERAS", kicker))
            story.append(Paragraph(TITLE, h1))
            story.append(Spacer(1, 2))
            story.append(Paragraph(SUBTITLE, ParagraphStyle(
                "Sub", parent=body, fontName="Helvetica", fontSize=10.5,
                textColor=ACCENT, spaceAfter=8)))
            story.append(Paragraph(INTRO, body))
            story.append(Spacer(1, 2))

        story.append(Paragraph(
            "ERA %d &nbsp;&nbsp;|&nbsp;&nbsp; %s" % (era.number, era.span.upper()), kicker))
        story.append(Paragraph(era.name, ParagraphStyle(
            "EraH", parent=h2, fontSize=15, leading=18, spaceBefore=0, spaceAfter=4)))
        story.append(Paragraph(era.lede, lede))

        for heading, text in era.sections:
            story.append(Paragraph(heading, h3))
            story.append(Paragraph(text, body))

        rows = [[Paragraph("<b>DATE</b>", caption), Paragraph("<b>EVENT</b>", caption),
                 Paragraph("<b>SIGNIFICANCE</b>", caption)]]
        for d, e, s in era.events:
            rows.append([Paragraph(d, ParagraphStyle("d", parent=body, fontSize=8.2,
                                                     leading=10.5, spaceAfter=0)),
                         Paragraph(e, ParagraphStyle("e", parent=body, fontSize=8.2,
                                                     leading=10.5, spaceAfter=0)),
                         Paragraph(s, ParagraphStyle("s", parent=body, fontSize=8.2,
                                                     leading=10.5, spaceAfter=0,
                                                     textColor=MUTED))])
        table = Table(rows, colWidths=[2.55 * cm, 5.4 * cm, doc.width - 7.95 * cm],
                      repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), LIGHT),
            ("LINEBELOW", (0, 0), (-1, 0), 0.8, ACCENT),
            ("LINEBELOW", (0, 1), (-1, -1), 0.25, RULE),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 3.2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3.2),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(Spacer(1, 4))
        story.append(KeepTogether([Paragraph("Key events of the era", caption), Spacer(1, 2), table]))

        if i == 4:
            story.append(Spacer(1, 5))
            story.append(Paragraph("Reflections", h3))
            story.append(Paragraph(CLOSING, body))
            story.append(Spacer(1, 5))
            story.append(Paragraph("Selected sources", h3))
            story.append(Paragraph(" &nbsp;&bull;&nbsp; ".join(SOURCES), ParagraphStyle(
                "src", parent=body, fontSize=7.4, leading=9.4, spaceAfter=0)))

        if era.number in STATS:
            cells = []
            for value, label in STATS[era.number]:
                cells.append(Paragraph(
                    '<font size="13" color="#8B5E34"><b>%s</b></font><br/>'
                    '<font size="7.6" color="#6B6259">%s</font>' % (value, label),
                    ParagraphStyle("stat", parent=body, alignment=TA_LEFT,
                                   leading=10, spaceAfter=0)))
            strip = Table([cells], colWidths=[doc.width / 3.0] * 3)
            strip.setStyle(TableStyle([
                ("LINEABOVE", (0, 0), (-1, 0), 0.7, RULE),
                ("LINEBELOW", (0, 0), (-1, 0), 0.7, RULE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            story.append(Spacer(1, 8))
            story.append(strip)

        if i < 4:
            box = Table([[Paragraph(
                '<font color="#8B5E34"><b>LEGACY</b></font>&nbsp;&nbsp;' + era.legacy, body)]],
                colWidths=[doc.width])
            box.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
                ("LINEBEFORE", (0, 0), (0, -1), 2.2, ACCENT),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            story.append(Spacer(1, 10))
            story.append(box)
            story.append(PageBreak())

    doc.build(story)


# -------------------------------------------------------------------------- DOCX
def add_page_number_footer(section):
    paragraph = section.footer.paragraphs[0]
    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = paragraph.add_run("Page ")
    run.font.size = Pt(8)
    run.font.color.rgb = RGBColor(0x6B, 0x62, 0x59)
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), "PAGE")
    r = OxmlElement("w:r")
    rpr = OxmlElement("w:rPr")
    sz = OxmlElement("w:sz")
    sz.set(qn("w:val"), "16")
    rpr.append(sz)
    r.append(rpr)
    t = OxmlElement("w:t")
    t.text = "1"
    r.append(t)
    fld.append(r)
    paragraph._p.append(fld)
    tail = paragraph.add_run(" of 5")
    tail.font.size = Pt(8)
    tail.font.color.rgb = RGBColor(0x6B, 0x62, 0x59)


def shade(cell, hex_fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_fill)
    tcPr.append(shd)


def build_docx():
    doc = Document()
    sec = doc.sections[0]
    sec.page_height = Cm(27.94)
    sec.page_width = Cm(21.59)
    sec.top_margin = Cm(1.9)
    sec.bottom_margin = Cm(1.9)
    sec.left_margin = Cm(2.2)
    sec.right_margin = Cm(2.2)

    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(10.5)
    normal.paragraph_format.space_after = Pt(5)
    normal.paragraph_format.line_spacing = 1.08

    for name, size, color in (("Heading 1", 22, "2E2A26"),
                              ("Heading 2", 16, "8B5E34"),
                              ("Heading 3", 11, "2E2A26")):
        st = doc.styles[name]
        st.font.name = "Calibri"
        st.font.size = Pt(size)
        st.font.bold = True
        st.font.color.rgb = RGBColor.from_string(color)

    add_page_number_footer(sec)

    kicker = doc.add_paragraph()
    r = kicker.add_run("HUMAN HISTORY IN FIVE ERAS")
    r.bold = True
    r.font.size = Pt(9)
    r.font.color.rgb = RGBColor(0x8B, 0x5E, 0x34)
    kicker.paragraph_format.space_after = Pt(2)

    doc.add_heading(TITLE, level=1)
    p = doc.add_paragraph()
    r = p.add_run(SUBTITLE)
    r.italic = True
    r.font.size = Pt(11.5)
    r.font.color.rgb = RGBColor(0x8B, 0x5E, 0x34)
    p.paragraph_format.space_after = Pt(10)

    doc.add_paragraph(INTRO)

    for i, era in enumerate(ERAS):
        if i > 0:
            doc.add_page_break()
        k = doc.add_paragraph()
        r = k.add_run("ERA %d  |  %s" % (era.number, era.span.upper()))
        r.bold = True
        r.font.size = Pt(9)
        r.font.color.rgb = RGBColor(0x8B, 0x5E, 0x34)
        k.paragraph_format.space_after = Pt(2)

        doc.add_heading(era.name, level=2)
        lede = doc.add_paragraph()
        r = lede.add_run(era.lede)
        r.italic = True
        r.font.color.rgb = RGBColor(0x6B, 0x62, 0x59)
        lede.paragraph_format.space_after = Pt(9)

        for heading, text in era.sections:
            doc.add_heading(heading, level=3)
            doc.add_paragraph(text)

        cap = doc.add_paragraph()
        r = cap.add_run("Key events of the era")
        r.italic = True
        r.font.size = Pt(8.5)
        r.font.color.rgb = RGBColor(0x6B, 0x62, 0x59)
        cap.paragraph_format.space_after = Pt(2)

        table = doc.add_table(rows=1, cols=3)
        table.style = "Table Grid"
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        widths = (Cm(2.9), Cm(6.0), Cm(8.2))
        hdr = table.rows[0].cells
        for j, label in enumerate(("DATE", "EVENT", "SIGNIFICANCE")):
            hdr[j].text = ""
            run = hdr[j].paragraphs[0].add_run(label)
            run.bold = True
            run.font.size = Pt(8)
            shade(hdr[j], "F3ECE1")
        for d, e, s in era.events:
            cells = table.add_row().cells
            for j, txt in enumerate((d, e, s)):
                cells[j].text = ""
                run = cells[j].paragraphs[0].add_run(txt)
                run.font.size = Pt(8.5)
                if j == 2:
                    run.font.color.rgb = RGBColor(0x6B, 0x62, 0x59)
        for row in table.rows:
            for j, cell in enumerate(row.cells):
                cell.width = widths[j]
                cell.paragraphs[0].paragraph_format.space_after = Pt(1)

        if era.number in STATS:
            sp = doc.add_paragraph()
            sp.paragraph_format.space_before = Pt(8)
            for k, (value, label) in enumerate(STATS[era.number]):
                if k:
                    r = sp.add_run("     |     ")
                    r.font.size = Pt(9)
                    r.font.color.rgb = RGBColor(0xD8, 0xC7, 0xB2)
                r = sp.add_run(value)
                r.bold = True
                r.font.size = Pt(11)
                r.font.color.rgb = RGBColor(0x8B, 0x5E, 0x34)
                r = sp.add_run("  " + label)
                r.font.size = Pt(8)
                r.font.color.rgb = RGBColor(0x6B, 0x62, 0x59)

        if i < 4:
            lp = doc.add_paragraph()
            lp.paragraph_format.space_before = Pt(10)
            r = lp.add_run("LEGACY  ")
            r.bold = True
            r.font.size = Pt(9)
            r.font.color.rgb = RGBColor(0x8B, 0x5E, 0x34)
            r = lp.add_run(era.legacy)
            r.font.size = Pt(9.5)
            r.italic = True

        if i == 4:
            doc.add_heading("Reflections", level=3)
            doc.add_paragraph(CLOSING)
            doc.add_heading("Selected sources", level=3)
            for s in SOURCES:
                bp = doc.add_paragraph(s, style="List Bullet")
                for run in bp.runs:
                    run.font.size = Pt(9)

    doc.core_properties.title = TITLE
    doc.core_properties.subject = "A five-page history of humanity"
    doc.core_properties.author = "Full-build"
    doc.save(DOCX_PATH)


# -------------------------------------------------------------------------- XLSX
TIMELINE = [
    ("c. 300,000 BCE", "First Homo sapiens appear", "Prehistory", "Africa", "Origin of our species"),
    ("c. 70,000 BCE", "Major dispersal out of Africa", "Prehistory", "Africa / Eurasia", "Humans settle across Eurasia"),
    ("c. 45,000 BCE", "Cave painting and carved figurines", "Prehistory", "Europe / Asia", "Symbolic culture and art"),
    ("c. 40,000 BCE", "Neanderthals disappear", "Prehistory", "Eurasia", "Homo sapiens becomes sole hominin"),
    ("c. 10,000 BCE", "Agriculture begins", "Prehistory", "Fertile Crescent", "Neolithic Revolution"),
    ("c. 9500 BCE", "Gobekli Tepe constructed", "Prehistory", "Anatolia", "Monumental ritual architecture"),
    ("c. 3500 BCE", "Cuneiform writing invented", "Ancient", "Mesopotamia", "Recorded history begins"),
    ("c. 3200 BCE", "Wheel and early cities", "Ancient", "Mesopotamia", "Urban and transport revolution"),
    ("c. 3000 BCE", "Egypt unified", "Ancient", "Egypt", "Pharaonic state established"),
    ("c. 2600 BCE", "Indus cities of Harappa and Mohenjo-daro", "Ancient", "South Asia", "Planned urban civilisation"),
    ("c. 2560 BCE", "Great Pyramid of Giza", "Ancient", "Egypt", "Peak of ancient engineering"),
    ("c. 1600 BCE", "Shang dynasty in China", "Ancient", "China", "First recorded Chinese dynasty"),
    ("c. 1200 BCE", "Bronze Age collapse", "Ancient", "Eastern Mediterranean", "Trade networks fracture"),
    ("776 BCE", "First Olympic Games", "Ancient", "Greece", "Panhellenic cultural tradition"),
    ("508 BCE", "Athenian democracy established", "Ancient", "Greece", "Citizens share political power"),
    ("336-323 BCE", "Reign of Alexander the Great", "Ancient", "Macedonia / Asia", "Hellenistic world created"),
    ("221 BCE", "Qin unifies China", "Ancient", "China", "Imperial China begins"),
    ("27 BCE", "Roman Empire founded", "Ancient", "Rome", "Augustus becomes first emperor"),
    ("476 CE", "Fall of the Western Roman Empire", "Ancient", "Europe", "End of classical antiquity"),
    ("622", "Hijra of Muhammad", "Medieval", "Arabia", "Islamic calendar begins"),
    ("800", "Charlemagne crowned emperor", "Medieval", "Europe", "Medieval Europe consolidated"),
    ("1088", "University of Bologna founded", "Medieval", "Italy", "Modern university tradition"),
    ("1206", "Mongol Empire founded", "Medieval", "Central Asia", "Largest contiguous land empire"),
    ("1347", "Black Death reaches Europe", "Medieval", "Europe", "Kills about a third of the population"),
    ("c. 1440", "Gutenberg's printing press", "Early modern", "Germany", "Knowledge mass-produced"),
    ("1453", "Fall of Constantinople", "Early modern", "Byzantium", "End of the Byzantine Empire"),
    ("1492", "Columbus reaches the Americas", "Early modern", "Atlantic", "Columbian Exchange begins"),
    ("1517", "Protestant Reformation begins", "Early modern", "Germany", "Western Christianity splits"),
    ("1543", "Copernicus publishes heliocentric model", "Early modern", "Poland", "Scientific Revolution starts"),
    ("1687", "Newton publishes Principia", "Early modern", "England", "Physics mathematised"),
    ("1769", "Watt's improved steam engine", "Industrial", "Britain", "Industrial power harnessed"),
    ("1776", "US Declaration of Independence", "Industrial", "North America", "Rights-based republic founded"),
    ("1789", "French Revolution begins", "Industrial", "France", "Monarchy and privilege challenged"),
    ("1804", "Napoleon crowned emperor", "Industrial", "France", "Revolutionary wars spread"),
    ("1830s", "Railway age begins", "Industrial", "Europe / USA", "Land transport transformed"),
    ("1859", "Darwin publishes Origin of Species", "Industrial", "Britain", "Evolution explains life"),
    ("1861-65", "American Civil War", "Industrial", "USA", "Slavery abolished, union preserved"),
    ("1914-18", "World War I", "Industrial", "Global", "Industrialised mass warfare"),
    ("1929", "Great Depression begins", "Industrial", "Global", "World economy collapses"),
    ("1939-45", "World War II", "Industrial", "Global", "Total war and the atomic age"),
    ("1945", "United Nations founded", "Modern", "Global", "Rules-based world order"),
    ("1947", "India and Pakistan independent", "Modern", "South Asia", "Decolonisation accelerates"),
    ("1949", "People's Republic of China founded", "Modern", "China", "New global power emerges"),
    ("1957", "Sputnik launched", "Modern", "USSR", "Space age begins"),
    ("1969", "Apollo 11 Moon landing", "Modern", "USA", "Humans walk on the Moon"),
    ("1989", "Berlin Wall falls", "Modern", "Europe", "Cold War ends in Europe"),
    ("1991", "USSR dissolves; World Wide Web public", "Modern", "Global", "Information age begins"),
    ("2001", "September 11 attacks", "Modern", "USA", "Global security redefined"),
    ("2008", "Global financial crisis", "Modern", "Global", "Banking system stress-tested"),
    ("2020-23", "COVID-19 pandemic", "Modern", "Global", "Health and work transformed"),
    ("2022-", "Generative AI boom", "Modern", "Global", "Machine intelligence spreads"),
]

ERAS_TABLE = [
    ("1. Prehistory", "c. 300,000 BCE", "c. 10,000 BCE", "c. 290,000 years",
     "Foraging, stone tools, fire, art, migration", "Homo sapiens, language, cave art, agriculture"),
    ("2. Ancient World", "c. 3500 BCE", "500 CE", "c. 4,000 years",
     "Cities, writing, empires, world religions", "Cuneiform, pyramids, democracy, Silk Road"),
    ("3. Middle Ages & Early Modern", "500 CE", "1800 CE", "c. 1,300 years",
     "Faiths, feudalism, trade, exploration", "Printing, Renaissance, Reformation, Columbian Exchange"),
    ("4. Revolutions & Industry", "1750 CE", "1945 CE", "c. 195 years",
     "Industry, nationalism, empire, total war", "Steam, railways, electricity, world wars"),
    ("5. Modern World", "1945 CE", "present", "c. 80 years",
     "Cold War, decolonisation, globalisation", "Computing, internet, genomics, AI"),
]

INVENTIONS = [
    ("Stone tools", "c. 2.6 million BCE", "Africa", "Hunting and food processing"),
    ("Controlled fire", "c. 400,000 BCE", "Africa / Eurasia", "Cooking, warmth, protection"),
    ("Sewn clothing", "c. 50,000 BCE", "Eurasia", "Survival in cold climates"),
    ("Farming and herding", "c. 10,000 BCE", "Fertile Crescent", "Food surplus and settlement"),
    ("Pottery", "c. 9,000 BCE", "Asia", "Storage and cooking"),
    ("Writing (cuneiform)", "c. 3200 BCE", "Sumer", "Records and administration"),
    ("Wheel", "c. 3200 BCE", "Mesopotamia", "Transport and machinery"),
    ("Iron working", "c. 1200 BCE", "Near East", "Stronger tools and weapons"),
    ("Paper", "c. 105 CE", "China", "Cheap writing material"),
    ("Printing press", "c. 1440 CE", "Germany", "Mass reproduction of texts"),
    ("Telescope", "1608 CE", "Netherlands", "Astronomy transformed"),
    ("Steam engine", "1712 / 1769 CE", "Britain", "Industrial power"),
    ("Vaccination", "1796 CE", "Britain", "Disease prevention"),
    ("Electricity grid", "1880s CE", "USA / Europe", "Power for homes and industry"),
    ("Airplane", "1903 CE", "USA", "Global travel"),
    ("Antibiotics (penicillin)", "1928 CE", "Britain", "Bacterial infections treated"),
    ("Transistor", "1947 CE", "USA", "Modern electronics"),
    ("Personal computer", "1970s-80s CE", "USA", "Computing for everyone"),
    ("World Wide Web", "1989-91 CE", "Switzerland", "Global information network"),
    ("Smartphone", "2007 CE", "USA", "Mobile internet era"),
    ("mRNA vaccines", "2020 CE", "Global", "Rapid pandemic response"),
    ("Generative AI", "2022 CE", "Global", "Machine-created text and images"),
]

POPULATION = [
    (10000, 4_000_000, "BCE estimate"),
    (1, 200_000_000, "Roman-era estimate"),
    (1000, 300_000_000, "Medieval estimate"),
    (1500, 500_000_000, "Early modern estimate"),
    (1800, 1_000_000_000, "Industrial Revolution"),
    (1927, 2_000_000_000, "Two billion reached"),
    (1960, 3_000_000_000, "Post-war boom"),
    (1974, 4_000_000_000, "Four billion reached"),
    (1987, 5_000_000_000, "Five billion reached"),
    (1999, 6_000_000_000, "Six billion reached"),
    (2011, 7_000_000_000, "Seven billion reached"),
    (2022, 8_000_000_000, "Eight billion reached"),
]


def style_header(ws, row=1, ncols=None):
    ncols = ncols or ws.max_column
    fill = PatternFill("solid", fgColor="2E2A26")
    thin = Side(style="thin", color="D8C7B2")
    for c in range(1, ncols + 1):
        cell = ws.cell(row=row, column=c)
        cell.font = Font(bold=True, color="FFFFFF", size=11)
        cell.fill = fill
        cell.alignment = Alignment(vertical="center", horizontal="left")
        cell.border = Border(bottom=thin)


def build_xlsx():
    wb = openpyxl.Workbook()
    thin = Side(style="thin", color="E1D5C4")
    border = Border(bottom=thin)

    # Overview
    ws = wb.active
    ws.title = "Overview"
    ws.sheet_properties.tabColor = "8B5E34"
    ws.column_dimensions["A"].width = 26
    ws.column_dimensions["B"].width = 90
    ws["A1"] = TITLE
    ws["A1"].font = Font(bold=True, size=20, color="2E2A26")
    ws.merge_cells("A1:B1")
    ws["A2"] = SUBTITLE
    ws["A2"].font = Font(italic=True, size=11, color="8B5E34")
    ws.merge_cells("A2:B2")
    ws["A3"] = "A five-part reference workbook covering c. 300,000 BCE to the present."
    ws["A3"].font = Font(size=10, color="6B6259")
    ws.merge_cells("A3:B3")
    ws["A5"] = "Workbook contents"
    ws["A5"].font = Font(bold=True, size=12, color="2E2A26")
    rows = [
        ("Timeline", "52 dated events from prehistory to the present"),
        ("Eras", "The five eras covered by the PDF and Word versions"),
        ("Inventions", "22 transformative technologies and their impact"),
        ("Population", "World population milestones with a chart"),
        ("Sources", "Selected references for further reading"),
        ("Document info", "Title, coverage, generated date and formats"),
    ]
    for i, (name, desc) in enumerate(rows, start=6):
        ws.cell(row=i, column=1, value=name).font = Font(bold=True, color="8B5E34")
        ws.cell(row=i, column=2, value=desc)
        for c in (1, 2):
            ws.cell(row=i, column=c).border = border

    # Timeline
    ws = wb.create_sheet("Timeline")
    ws.sheet_properties.tabColor = "8B5E34"
    headers = ["Date", "Event", "Era", "Region", "Significance"]
    ws.append(headers)
    for row in TIMELINE:
        ws.append(list(row))
    style_header(ws)
    widths = [16, 42, 15, 22, 46]
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = "A1:E%d" % (len(TIMELINE) + 1)
    for r in range(2, len(TIMELINE) + 2):
        for c in range(1, 6):
            cell = ws.cell(row=r, column=c)
            cell.alignment = Alignment(vertical="top", wrap_text=True)
            cell.border = border
        if r % 2 == 0:
            for c in range(1, 6):
                ws.cell(row=r, column=c).fill = PatternFill("solid", fgColor="FAF6F0")

    # Eras
    ws = wb.create_sheet("Eras")
    ws.sheet_properties.tabColor = "A97B50"
    ws.append(["Era", "Start", "End", "Duration", "Defining features",
               "Key developments", "Legacy"])
    for row, era in zip(ERAS_TABLE, ERAS):
        ws.append(list(row) + [era.legacy])
    style_header(ws)
    for i, w in enumerate([30, 16, 14, 18, 40, 46, 56], start=1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = "A2"
    for r in range(2, len(ERAS_TABLE) + 2):
        for c in range(1, 8):
            cell = ws.cell(row=r, column=c)
            cell.alignment = Alignment(vertical="top", wrap_text=True)
            cell.border = border

    # Inventions
    ws = wb.create_sheet("Inventions")
    ws.sheet_properties.tabColor = "C08A5A"
    ws.append(["Innovation", "Approx. date", "Region", "Impact"])
    for row in INVENTIONS:
        ws.append(list(row))
    style_header(ws)
    for i, w in enumerate([30, 20, 20, 52], start=1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = "A1:D%d" % (len(INVENTIONS) + 1)
    for r in range(2, len(INVENTIONS) + 2):
        for c in range(1, 5):
            cell = ws.cell(row=r, column=c)
            cell.alignment = Alignment(vertical="top", wrap_text=True)
            cell.border = border

    # Population
    ws = wb.create_sheet("Population")
    ws.sheet_properties.tabColor = "D2A679"
    ws.append(["Year", "World population", "Note"])
    for year, pop, note in POPULATION:
        ws.append([year, pop, note])
    style_header(ws)
    ws.column_dimensions["A"].width = 12
    ws.column_dimensions["B"].width = 22
    ws.column_dimensions["C"].width = 30
    for r in range(2, len(POPULATION) + 2):
        ws.cell(row=r, column=1).number_format = "0"
        ws.cell(row=r, column=2).number_format = "#,##0"
        ws.cell(row=r, column=2).alignment = Alignment(horizontal="right")
    chart = LineChart()
    chart.title = "World population milestones"
    chart.y_axis.title = "People"
    chart.x_axis.title = "Year"
    chart.height = 9
    chart.width = 18
    data = Reference(ws, min_col=2, min_row=1, max_row=len(POPULATION) + 1)
    cats = Reference(ws, min_col=1, min_row=2, max_row=len(POPULATION) + 1)
    chart.add_data(data, titles_from_data=True)
    chart.set_categories(cats)
    chart.legend = None
    chart.series[0].graphicalProperties.line.width = 28000
    chart.series[0].graphicalProperties.line.solidFill = "8B5E34"
    ws.add_chart(chart, "E2")

    # Sources
    ws = wb.create_sheet("Sources")
    ws.sheet_properties.tabColor = "E4C9A8"
    ws.append(["#", "Reference"])
    for i, s in enumerate(SOURCES, start=1):
        ws.append([i, s])
    style_header(ws)
    ws.column_dimensions["A"].width = 6
    ws.column_dimensions["B"].width = 100
    for r in range(2, len(SOURCES) + 2):
        ws.cell(row=r, column=2).alignment = Alignment(wrap_text=True, vertical="top")

    # Document info
    ws = wb.create_sheet("Document info")
    ws.sheet_properties.tabColor = "EFE2D2"
    ws.column_dimensions["A"].width = 26
    ws.column_dimensions["B"].width = 60
    info = [
        ("Title", TITLE),
        ("Subtitle", SUBTITLE),
        ("Coverage", "c. 300,000 BCE to the present"),
        ("Eras covered", "5"),
        ("PDF pages", "5"),
        ("Word pages", "5 (one era per page)"),
        ("Excel sheets", "7 (including Overview)"),
        ("Timeline entries", str(len(TIMELINE))),
        ("Inventions listed", str(len(INVENTIONS))),
        ("Generated", date.today().isoformat()),
        ("Companion files", "human-history.pdf, human-history.docx, human-history.xlsx"),
    ]
    ws["A1"] = "Document information"
    ws["A1"].font = Font(bold=True, size=14, color="2E2A26")
    for i, (k, v) in enumerate(info, start=3):
        a = ws.cell(row=i, column=1, value=k)
        a.font = Font(bold=True, color="8B5E34")
        a.border = border
        b = ws.cell(row=i, column=2, value=v)
        b.border = border
        b.alignment = Alignment(wrap_text=True, vertical="top")

    for sheet in wb.worksheets:
        sheet.sheet_view.showGridLines = False
        sheet.page_setup.orientation = "landscape"
        sheet.page_setup.fitToWidth = 1
        sheet.sheet_properties.pageSetUpPr.fitToPage = True

    wb.properties.title = TITLE
    wb.properties.creator = "Full-build"
    wb.properties.subject = "A five-page history of humanity"
    wb.save(XLSX_PATH)


if __name__ == "__main__":
    build_pdf()
    build_docx()
    build_xlsx()
    for path in (PDF_PATH, DOCX_PATH, XLSX_PATH):
        print(path, os.path.getsize(path))
