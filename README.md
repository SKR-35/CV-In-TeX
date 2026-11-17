![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=blue)
![Pandoc](https://img.shields.io/badge/Pandoc-Markdown%20to%20LaTeX-5277C3)
![XeLaTeX](https://img.shields.io/badge/PDF-XeLaTeX-008080)
[![CI](https://img.shields.io/github/actions/workflow/status/SKR-35/CV-In-TeX/python-tests.yml?branch=master&label=CI&logo=githubactions&logoColor=white)](https://github.com/SKR-35/CV-In-TeX/actions/workflows/python-tests.yml)

# CV-in-TeX

**Write in Markdown. Publish with LaTeX.**

CV-in-TeX is a lightweight, open-source command-line tool for turning a structured Markdown résumé into a polished PDF using **Pandoc** and **XeLaTeX**. It supports a two-column CV layout and an optional landscape project portfolio, without requiring you to edit LaTeX directly.

The repository includes a complete, fictional **John Smith** example so you can try the workflow immediately and adapt the content to your own needs.

## Features

- **Markdown-first authoring:** keep résumé content in an editable, versionable text file.
- **Two-column CV pages:** separate sidebar information from the main professional narrative.
- **Optional project portfolio:** generate a landscape, four-column project table after the CV.
- **PDF and TeX output:** produce a ready-to-share PDF and retain the generated LaTeX source.
- **Eight color themes:** customize accent colors without changing Markdown content or document structure.
- **Flexible input/output paths:** read Markdown from any local directory; write results next to the source or to a chosen output folder.
- **Reproducible Python tooling:** manage the development environment with [uv](https://docs.astral.sh/uv/).
- **Quality checks:** pytest tests and a GitHub Actions workflow for the example build.

## Requirements

| Tool | Purpose |
| --- | --- |
| [Python](https://www.python.org/) 3.11+ | Run the build script |
| [uv](https://docs.astral.sh/uv/) | Manage the Python environment |
| [Pandoc](https://pandoc.org/installing.html) | Convert Markdown fragments to LaTeX |
| XeLaTeX ([MiKTeX](https://miktex.org/) or [TeX Live](https://www.tug.org/texlive/)) | Compile the final PDF |

Pandoc and XeLaTeX must be available on your system `PATH`; **uv does not install them**.

Check your setup:

```powershell
pandoc --version
xelatex --version
```

## Quick start

Clone the repository, open a terminal in the project directory and install the development dependencies:

```powershell
uv sync
```

Build the bundled sample CV:

```powershell
uv run python scripts/build_cv.py --input examples/john_smith_cv.md --output-dir dist
```

The generated files are:

```text
 dist/
 ├── john_smith_cv.pdf
 └── john_smith_cv.tex
```

You can also provide a Markdown file outside the repository. When `--output-dir` is omitted, the PDF and TeX are written **next to the input file**:

```powershell
uv run python scripts/build_cv.py --input "D:\Documents\Resume\resume.md"
```

To choose another output directory:

```powershell
uv run python scripts/build_cv.py --input "D:\Documents\Resume\resume.md" --output-dir "D:\Documents\Exports"
```

## Color themes

The default is **monochrome** (`none`). Choose one of eight optional color palettes using `--theme`. Theme selection changes accent colors only; Markdown content and document layout remain unchanged.

| Theme | CLI value | Accent colors |
| --- | --- | --- |
| Monochrome (default) | `none` | `#B0B0B0` · `#4A4A4A` |
| Sage Green | `sage-green` | `#A9D18E` · `#52734D` |
| Forest Green | `forest-green` | `#56846B` · `#285640` |
| Navy Blue | `navy-blue` | `#547DA3` · `#254663` |
| Slate Blue | `slate-blue` | `#8999B6` · `#485C80` |
| Teal | `teal` | `#62A9A1` · `#286E69` |
| Burgundy | `burgundy` | `#9B6270` · `#643644` |
| Warm Sand | `warm-sand` | `#D4B98C` · `#80643C` |
| Graphite | `graphite` | `#858B91` · `#3B4249` |

Build the example CV with a chosen palette:

```powershell
uv run python scripts/build_cv.py --input examples/john_smith_cv.md --theme navy-blue --output-dir dist
```

Omit `--theme` to generate the default monochrome CV. You can also specify `--theme none` explicitly.

## Markdown document structure

The generator uses simple Markdown plus HTML comment markers to identify page and column boundaries:

```markdown
# John Smith
> Data Scientist | Software Engineer

<!-- PAGE 1 -->
<!-- SIDEBAR -->
## CONTACT
john.smith@example.com

## SKILLS
Python, SQL, R

<!-- MAIN -->
## SUMMARY
Data professional focused on reliable analytics.

## EXPERIENCE
**Data Scientist (2023 – Present)**

- Built analytical workflows and automated reporting.
```

For another CV page, add `<!-- PAGE 2 -->` with its own `<!-- SIDEBAR -->` and `<!-- MAIN -->` sections. Each page must contain exactly one sidebar marker and one main marker.

### Optional project portfolio

Add `<!-- PORTFOLIO -->` after the CV pages, followed by project entries:

```markdown
<!-- PORTFOLIO -->
### Data Quality Monitor
**Description:** Checks datasets against defined quality rules.

**Responsibilities/Details:**
- Implemented validation checks.
- Documented test results.

**Tools Used:** Python, SQL, pytest
```

Each project becomes a row in a landscape table with four columns: **Project Name**, **Project Description**, **Responsibilities/Details** and **Tools Used**. For the full syntax, see [`examples/john_smith_cv.md`](examples/john_smith_cv.md).

## Project layout

```text
CV-in-TeX/
├── examples/
│   └── john_smith_cv.md
├── scripts/
│   └── build_cv.py
├── templates/
│   └── cv.tex
├── tests/
│   └── test_build_cv.py
├── .github/workflows/
│   └── python-tests.yml
├── pyproject.toml
├── DECISIONS.md
└── README.md
```

## Development

Run the test suite:

```powershell
uv run pytest -v
```

Check linting and formatting with [Ruff](https://docs.astral.sh/ruff/):

```powershell
uv run ruff check .
uv run ruff format --check .
```

Apply automatic fixes or formatting when needed:

```powershell
uv run ruff check . --fix
uv run ruff format .
```

The GitHub Actions workflow runs the Python tests and builds the fictional sample PDF on Ubuntu. Pandoc and XeLaTeX are installed separately in CI.

## Notes and limitations

- CV pages use explicit `PAGE`, `SIDEBAR` and `MAIN` markers; automatic pagination of the two-column CV is not implemented.
- The portfolio table can span pages as needed.
- Visual appearance depends on the LaTeX template and available TeX packages/fonts.
- The tool is a document generator, not a graphical résumé editor.