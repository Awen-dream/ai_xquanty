import json
from pathlib import Path


def _load_notebook() -> dict:
    notebook_path = Path("docs/superpowers/specs/course/q2-what-to-buy/notebooks/q2-what-to-buy.ipynb")
    return json.loads(notebook_path.read_text(encoding="utf-8"))


def _cell_source(cell: dict) -> str:
    source = cell.get("source", "")
    if isinstance(source, list):
        return "".join(source)
    return source


def test_q2_notebook_prerequisites_reference_env_setup_spec() -> None:
    notebook = _load_notebook()
    intro = _cell_source(notebook["cells"][0])
    assert "docs/superpowers/specs/course/env-setup/spec-01-env-setup-mac.md" in intro
    assert "pip install open-xquant[yfinance,akshare]" not in intro


def test_q2_notebook_uses_factor_downloader_for_world_bank_gdp() -> None:
    notebook = _load_notebook()
    code = "\n".join(
        _cell_source(cell)
        for cell in notebook["cells"]
        if cell.get("cell_type") == "code"
    )
    assert "from oxq.data import FactorDownloader, WorldBankDownloader, read_factor" in code
    assert "factor_dl = FactorDownloader(WorldBankDownloader(), sub=\"macro\")" in code
    assert "factor_dl.download(\"gdp\", \"2020\", \"2024\", countries=countries)" in code
    assert "wb.download(\"gdp\", countries=countries, start_year=2020, end_year=2024)" not in code


def test_q2_notebook_exposes_live_validation_config() -> None:
    notebook = _load_notebook()
    code = _cell_source(notebook["cells"][2])
    assert 'NOTEBOOK_MODE = "teaching"' in code
    assert 'VALIDATION_END = "2026-07-29"' in code
    assert 'FRESHNESS_POLICY = "allow_stale"' in code


def test_q2_notebook_contains_out_of_sample_validation_section() -> None:
    notebook = _load_notebook()
    all_text = "\n".join(_cell_source(cell) for cell in notebook["cells"])
    assert "## Step 4: 截至 VALIDATION_END 的样本外验证" in all_text
    assert "validation_start = \"2026-03-04\"" in all_text
    assert 'if FRESHNESS_POLICY == "strict"' in all_text
    assert "数据不是截至 VALIDATION_END 的最新结果" in all_text


def test_q2_notebook_records_july_proxy_validation_interpretation() -> None:
    notebook = _load_notebook()
    all_text = "\n".join(_cell_source(cell) for cell in notebook["cells"])
    assert "2026-07-01 到 2026-07-29 的代理验证" in all_text
    assert "单押沪深300：累计收益 -6.82%" in all_text
    assert "三资产等权组合：累计收益 -3.74%" in all_text


def test_q2_notebook_code_cells_compile() -> None:
    notebook = _load_notebook()
    for index, cell in enumerate(notebook["cells"]):
        if cell.get("cell_type") != "code":
            continue
        source = _cell_source(cell)
        compile(source, f"q2-cell-{index}", "exec")
