# Full-build

A small collection of front-end experiments and generated reference documents — built to
exercise Dark Matter end to end.

The repository has two parts:

1. **Sentinel-01** — a single-page 3D web demo in which a procedural character tracks your
   cursor with its head, shoulders and gaze.
2. **Human history kit** — a matching PDF, Word document, Excel workbook and PowerPoint
   deck that summarise roughly 300,000 years of human history.

## Human history kit

All four files are generated from the same content so the story stays consistent:

| File | Format | Length | What it contains |
| --- | --- | --- | --- |
| [`human-history.pdf`](human-history.pdf) | PDF | 5 pages | One page per era, key-event tables, statistics and legacy notes |
| [`human-history.docx`](human-history.docx) | Word | 5 pages | The same five eras as an editable document |
| [`human-history.xlsx`](human-history.xlsx) | Excel | 7 sheets | Timeline, eras, inventions, population chart, sources and document info |
| [`human-history.pptx`](human-history.pptx) | PowerPoint | 4 slides | A visual overview of human origins, the five eras and the modern world |

Nothing is fetched at runtime: every asset is local, so the files open offline.

### Regenerating the documents

The PDF, Word and Excel files are produced by one script; the deck has its own generator.

```bash
pip install reportlab openpyxl python-docx python-pptx

python scripts/generate_history_docs.py   # human-history.pdf / .docx / .xlsx
python scripts/generate_human_ppt.py      # human-history.pptx
```

Both scripts write their output to the repository root and print the resulting file paths
and sizes. Dates use BCE/CE and are approximate.

## Sentinel-01 web demo

Open [`index.html`](index.html) in a browser, or serve the folder locally to avoid any
file-protocol quirks:

```bash
python3 -m http.server 8000
# then visit http://localhost:8000
```

The page loads Three.js from `vendor/three.min.js`, so no network connection or build step
is required. If WebGL is unavailable the hero gracefully falls back to a static layout.
Move the cursor across the stage to make the character follow you.

## Project structure

```text
.
├── index.html                      # Sentinel-01 landing page
├── css/styles.css                  # Site styles
├── js/main.js                      # 3D scene, cursor tracking, interactions
├── vendor/three.min.js             # Vendored Three.js
├── assets/                         # Self-hosted web fonts
├── scripts/
│   ├── generate_history_docs.py    # Builds the PDF, Word and Excel files
│   └── generate_human_ppt.py       # Builds the PowerPoint deck
├── human-history.pdf               # Generated deliverables
├── human-history.docx
├── human-history.xlsx
├── human-history.pptx
└── .github/workflows/              # CI workflow for the Dark Matter agent
```

## Notes

- Generated documents use a warm cream/brown palette (`#8B5E34` on `#F3ECE1`) to match the
  human-history theme.
- The PowerPoint is intentionally short: four 16:9 slides, designed to be readable at a
  glance rather than a full transcript.
- There is no build tooling for the website — plain HTML, CSS and JavaScript only.
