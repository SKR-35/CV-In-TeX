import importlib.util
from pathlib import Path

import pytest

path = Path(__file__).resolve().parents[1] / "scripts" / "build_cv.py"
spec = importlib.util.spec_from_file_location("build_cv", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_parse_pages_and_portfolio():
    source = "# John Smith\n> Engineer\n<!-- PAGE 1 -->\n<!-- SIDEBAR -->\n## PHONE\nN/A\n<!-- MAIN -->\n## SUMMARY\nHello.\n<!-- PORTFOLIO -->\n### Demo\n**Description:** Demo description\n**Responsibilities/Details:**\n- Build\n**Tools Used:** Python\n"
    name, subtitle, pages, portfolio = module.parse_pages(source)
    assert (name, subtitle) == ("John Smith", "Engineer")
    assert len(pages) == 1
    assert module.parse_portfolio(portfolio)[0]["name"] == "Demo"


def test_missing_markers():
    with pytest.raises(ValueError, match="PAGE 1"):
        module.parse_pages("# John Smith\n> Engineer")


def test_escape_latex():
    assert module.latex_escape("R&D 100%") == r"R\&D 100\%"


def test_real_markdown_is_not_part_of_public_repo():
    root = Path(__file__).resolve().parents[1]
    assert not (root / "Archive" / "my_cv.md").exists()
