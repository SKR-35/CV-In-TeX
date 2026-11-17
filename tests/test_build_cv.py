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


def test_portfolio_tools_clean_separators():
    result = module.render_portfolio_cell(
        "- QlikView Server,; - QlikView SAP Connector,; - VBS", "tools"
    )
    assert "QlikView Server, QlikView SAP Connector, VBS" in result
    assert ";" not in result
    assert result.startswith(r"{\RaggedRight ")


def test_portfolio_details_have_no_list_top_spacing():
    result = module.render_portfolio_cell(
        "- First responsibility\n- Second responsibility", "details"
    )
    assert r"\textendash\ First responsibility" in result
    assert r"\par \textendash\ Second responsibility" in result
    assert r"\begin{itemize}" not in result


def test_theme_colors_and_content_are_independent():
    source = "# John Smith\n> Engineer\n<!-- PAGE 1 -->\n<!-- SIDEBAR -->\n## PHONE\nN/A\n<!-- MAIN -->\n## SUMMARY\nHello.\n"
    sage = module.make_tex(source, theme="sage-green")
    navy = module.make_tex(source, theme="navy-blue")
    assert r"\definecolor{accent}{HTML}{A9D18E}" in sage
    assert r"\definecolor{accent}{HTML}{547DA3}" in navy
    assert "John Smith" in sage and "John Smith" in navy
    assert "Hello." in sage and "Hello." in navy
    assert sage.replace("A9D18E", "547DA3").replace("52734D", "254663") == navy


def test_invalid_theme_rejected():
    with pytest.raises(ValueError, match="Unknown theme"):
        module.make_tex("# John Smith", theme="invalid")


def test_none_theme_is_monochrome_and_preserves_content():
    source = "# John Smith\n> Engineer\n<!-- PAGE 1 -->\n<!-- SIDEBAR -->\n## PHONE\nN/A\n<!-- MAIN -->\n## SUMMARY\nHello.\n"
    plain = module.make_tex(source, theme="none")
    sage = module.make_tex(source, theme="sage-green")
    assert sage != plain
    assert r"\definecolor{accent}{HTML}{B0B0B0}" in plain
    assert r"\definecolor{accentdark}{HTML}{4A4A4A}" in plain
    assert "John Smith" in plain and "Hello." in plain
    assert module.THEMES["none"] == ("B0B0B0", "4A4A4A")


def test_default_theme_is_none(monkeypatch):
    monkeypatch.setattr(module, "markdown_to_latex", lambda text: text)
    source = "# John Smith\n> Engineer\n<!-- PAGE 1 -->\n<!-- SIDEBAR -->\n## PHONE\nN/A\n<!-- MAIN -->\n## SUMMARY\nHello.\n"
    assert module.make_tex(source) == module.make_tex(source, theme="none")
    assert module.build.__kwdefaults__["theme"] == "none"
