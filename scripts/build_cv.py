"""Build a CV and optional landscape portfolio from a local Markdown source."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE_RE = re.compile(r"^<!--\s*PAGE\s+(\d+)\s*-->\s*$", re.M)
SECTION_RE = re.compile(r"^##\s+(.+?)\s*$", re.M)
PORTFOLIO_RE = re.compile(r"^<!--\s*PORTFOLIO\s*-->\s*$", re.M)

THEMES = {
    "sage-green": ("A9D18E", "52734D"),
    "forest-green": ("56846B", "285640"),
    "navy-blue": ("547DA3", "254663"),
    "slate-blue": ("8999B6", "485C80"),
    "teal": ("62A9A1", "286E69"),
    "burgundy": ("9B6270", "643644"),
    "warm-sand": ("D4B98C", "80643C"),
    "graphite": ("858B91", "3B4249"),
}


def latex_escape(s: str) -> str:
    return (
        s.replace("\\", r"\textbackslash{}")
        .replace("&", r"\&")
        .replace("%", r"\%")
        .replace("$", r"\$")
        .replace("#", r"\#")
        .replace("_", r"\_")
        .replace("{", r"\{")
        .replace("}", r"\}")
        .replace("~", r"\textasciitilde{}")
        .replace("^", r"\textasciicircum{}")
    )


def markdown_to_latex(text: str) -> str:
    if not text.strip():
        return ""
    p = subprocess.run(
        ["pandoc", "--from=gfm", "--to=latex", "--wrap=none"],
        input=text,
        text=True,
        capture_output=True,
        check=True,
        encoding="utf-8",
    )
    return p.stdout.strip()


def split_sections(text: str) -> list[tuple[str, str]]:
    matches = list(SECTION_RE.finditer(text))
    return [
        (
            m.group(1).strip(),
            text[m.end() : (matches[i + 1].start() if i + 1 < len(matches) else len(text))].strip(),
        )
        for i, m in enumerate(matches)
    ]


def render_sections(text: str, sidebar: bool = False) -> str:
    rendered = []
    for title, content in split_sections(text):
        cmd = "sideheading" if sidebar else "cvheading"
        rendered.append("\\" + cmd + "{" + latex_escape(title) + "}\n" + markdown_to_latex(content))
    return "\n".join(rendered)


def parse_pages(text: str) -> tuple[str, str, list[tuple[str, str]]]:
    portfolio = PORTFOLIO_RE.search(text)
    cv_text = text[: portfolio.start()] if portfolio else text
    portfolio_text = text[portfolio.end() :].strip() if portfolio else ""
    name = re.search(r"^#\s+(.+)$", cv_text, re.M)
    subtitle = re.search(r"^>\s+(.+)$", cv_text, re.M)
    if not name or not subtitle:
        raise ValueError("CV must contain a # Name and > Professional title")
    page_matches = list(PAGE_RE.finditer(cv_text))
    if not page_matches:
        raise ValueError("CV must contain <!-- PAGE 1 --> marker")
    pages = []
    for i, match in enumerate(page_matches):
        block = cv_text[
            match.end() : page_matches[i + 1].start() if i + 1 < len(page_matches) else len(cv_text)
        ]
        if block.count("<!-- SIDEBAR -->") != 1 or block.count("<!-- MAIN -->") != 1:
            raise ValueError(f"Page {i + 1} needs one SIDEBAR and one MAIN marker")
        sidebar = block.split("<!-- SIDEBAR -->", 1)[1].split("<!-- MAIN -->", 1)[0]
        main = block.split("<!-- MAIN -->", 1)[1]
        pages.append((sidebar, main))
    return name.group(1).strip(), subtitle.group(1).strip(), pages, portfolio_text


def parse_portfolio(md: str) -> list[dict[str, str]]:
    if not md:
        return []
    items = []
    chunks = re.split(r"^###\s+", md, flags=re.M)
    for chunk in chunks[1:]:
        lines = chunk.splitlines()
        name = lines[0].strip()
        if name == "Project Name":
            continue  # Repeated table header in some Word exports.
        fields = {"description": "", "details": "", "tools": ""}
        field = None
        for line in lines[1:]:
            match = re.match(
                r"^\*\*(Description|Responsibilities/Details|Tools Used):\*\*\s*(.*)$", line
            )
            if match:
                field = {
                    "Description": "description",
                    "Responsibilities/Details": "details",
                    "Tools Used": "tools",
                }[match.group(1)]
                if match.group(2):
                    fields[field] += match.group(2) + "\n"
            elif field:
                fields[field] += line + "\n"
        items.append({"name": name, **{k: v.strip() for k, v in fields.items()}})
    return items


def render_portfolio_cell(value: str, kind: str) -> str:
    """Render portfolio cells without Pandoc list spacing or justified tool names."""
    if kind == "tools":
        # Legacy Word-to-Markdown exports use `- Tool,; - Tool,; - Tool`.
        tools = [
            part.strip().lstrip("- ").rstrip(" ,;")
            for part in re.split(r";|\n", value)
            if part.strip().lstrip("- ").rstrip(" ,;")
        ]
        return r"{\RaggedRight " + latex_escape(", ".join(tools)) + r"\par}"
    if kind == "details":
        lines = [line.strip() for line in value.splitlines() if line.strip()]
        # Plain lines avoid itemize's topsep, which lowered this column's text.
        rendered = [
            r"\textendash\ " + latex_escape(line.removeprefix("-").strip()) for line in lines
        ]
        return r"{\RaggedRight " + r"\par ".join(rendered) + r"\par}"
    return r"{\RaggedRight " + markdown_to_latex(value) + r"\par}"


def make_tex(source: str, theme: str = "sage-green") -> str:
    if theme not in THEMES:
        raise ValueError(f"Unknown theme: {theme}. Available: {', '.join(THEMES)}")
    name, subtitle, pages, portfolio = parse_pages(source)
    template = (ROOT / "templates" / "cv.tex").read_text(encoding="utf-8")
    bodies = []
    for sidebar, main in pages:
        bodies.append(
            r"\begin{minipage}[t]{0.275\textwidth}"
            + "\n"
            + render_sections(sidebar, True)
            + "\n"
            + r"\end{minipage}\hfill"
            + "\n"
            + r"\begin{minipage}[t]{0.675\textwidth}"
            + "\n"
            + render_sections(main)
            + "\n"
            + r"\end{minipage}"
        )
    cv_body = "\n\\newpage\n".join(bodies)
    portfolio_rows = []
    for p in parse_portfolio(portfolio):
        cells = [render_portfolio_cell(p["name"], "name")]
        for key in ("description", "details", "tools"):
            cells.append(render_portfolio_cell(p[key], key))
        portfolio_rows.append(" & ".join(cells) + r" \\ \hline")
    portfolio_tex = ""
    if portfolio_rows:
        portfolio_tex = (
            r"\clearpage\begin{landscape}"
            + "\n"
            + r"\small\section*{Extended Projects Portfolio}"
            + "\n"
            + r"\begin{longtable}{|p{0.17\linewidth}|p{0.23\linewidth}|p{0.38\linewidth}|p{0.15\linewidth}|}"
            + "\n"
            + r"\hline\textbf{Project Name} & \textbf{Project Description} & \textbf{Responsibilities/Details} & \textbf{Tools Used} \\ \hline"
            + "\n"
            + r"\endfirsthead"
            + "\n"
            + r"\multicolumn{4}{l}{\textbf{Extended Projects Portfolio (continued)}}\\\hline"
            + "\n"
            + r"\textbf{Project Name} & \textbf{Project Description} & \textbf{Responsibilities/Details} & \textbf{Tools Used} \\ \hline"
            + "\n"
            + r"\endhead"
            + "\n"
            + "\n".join(portfolio_rows)
            + "\n"
            + r"\end{longtable}\end{landscape}"
        )
    light, dark = THEMES[theme]
    return (
        template.replace("%%ACCENT%%", light)
        .replace("%%ACCENT_DARK%%", dark)
        .replace("%%NAME%%", latex_escape(name))
        .replace("%%SUBTITLE%%", latex_escape(subtitle))
        .replace("%%CV_BODY%%", cv_body)
        .replace("%%PORTFOLIO%%", portfolio_tex)
    )


def build(
    source: Path, output_dir: Path, *, keep_tex: bool = True, theme: str = "sage-green"
) -> Path:
    source = source.expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(f"Input Markdown not found: {source}")
    for exe in ("pandoc", "xelatex"):
        if not shutil.which(exe):
            raise RuntimeError(f"{exe} is required on PATH (uv does not install it).")
    # Output defaults to the same private directory as the input. No source is copied into the repository.
    output_dir = output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="cv-in-tex-") as temp:
        work = Path(temp)
        tex = work / (source.stem + ".tex")
        tex.write_text(make_tex(source.read_text(encoding="utf-8"), theme=theme), encoding="utf-8")
        for _ in range(2):
            subprocess.run(
                [
                    "xelatex",
                    "-interaction=nonstopmode",
                    "-halt-on-error",
                    "-file-line-error",
                    f"-output-directory={work}",
                    str(tex),
                ],
                cwd=work,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
        pdf = work / (source.stem + ".pdf")
        if not pdf.exists():
            raise RuntimeError("XeLaTeX completed without creating a PDF")
        shutil.copy2(pdf, output_dir / pdf.name)
        if keep_tex:
            shutil.copy2(tex, output_dir / tex.name)
    return output_dir / pdf.name


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a CV PDF from Markdown; outputs alongside the input by default."
    )
    parser.add_argument(
        "--input", required=True, type=Path, help="Markdown source on any local drive"
    )
    parser.add_argument("--output-dir", type=Path, help="Defaults to the input Markdown directory")
    parser.add_argument(
        "--theme",
        choices=tuple(THEMES),
        default="sage-green",
        help="Color palette (default: sage-green)",
    )
    args = parser.parse_args()
    try:
        output = build(args.input, args.output_dir or args.input.parent, theme=args.theme)
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"Build failed: {exc}", file=sys.stderr)
        return 1
    print(f"Created: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
