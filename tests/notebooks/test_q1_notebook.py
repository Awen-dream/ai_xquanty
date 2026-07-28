import json
from pathlib import Path


def _load_notebook() -> dict:
    notebook_path = Path("docs/superpowers/specs/course/q1-how-to-profit/notebooks/q1-strategy.ipynb")
    return json.loads(notebook_path.read_text(encoding="utf-8"))


def _cell_source(cell: dict) -> str:
    source = cell.get("source", "")
    if isinstance(source, list):
        return "".join(source)
    return source


def test_q1_notebook_is_inside_course_specs_directory() -> None:
    notebook_path = Path("docs/superpowers/specs/course/q1-how-to-profit/notebooks/q1-strategy.ipynb")
    assert notebook_path.exists()
    assert notebook_path.parts[:5] == ("docs", "superpowers", "specs", "course", "q1-how-to-profit")


def test_q1_notebook_has_local_readme() -> None:
    readme_path = Path("docs/superpowers/specs/course/q1-how-to-profit/README.md")
    assert readme_path.exists()


def test_q1_notebook_intro_uses_current_spec_paths() -> None:
    notebook = _load_notebook()
    intro = _cell_source(notebook["cells"][0])
    assert "docs/superpowers/specs/course/env-setup/spec-01-env-setup-mac.md" in intro
    assert "setup/env-setup-spec.md" not in intro
    assert "复制到 TRAE 的 AI 助手中" not in intro


def test_q1_notebook_step_markdown_references_specs_instead_of_copying_to_trae() -> None:
    notebook = _load_notebook()
    markdown_sources = [
        _cell_source(cell)
        for cell in notebook["cells"]
        if cell.get("cell_type") == "markdown"
    ]
    joined = "\n".join(markdown_sources)
    assert "复制到 TRAE 的 AI 助手中" not in joined
    assert "docs/superpowers/specs/course/q1-how-to-profit/specs/spec-01-get-data.md" in joined
    assert "docs/superpowers/specs/course/q1-how-to-profit/specs/spec-07-overfitting.md" in joined


def test_q1_notebook_uses_non_overlapping_iloc_split() -> None:
    notebook = _load_notebook()
    code = "\n".join(
        _cell_source(cell)
        for cell in notebook["cells"]
        if cell.get("cell_type") == "code"
    )
    assert "train = df.iloc[:split_idx]" in code
    assert "test = df.iloc[split_idx:]" in code
    assert "train = df.loc[:split_date]" not in code
    assert "test = df.loc[split_date:]" not in code


def test_q1_notebook_contains_required_validation_assertions() -> None:
    notebook = _load_notebook()
    code = "\n".join(
        _cell_source(cell)
        for cell in notebook["cells"]
        if cell.get("cell_type") == "code"
    )
    required_assertions = [
        "assert isinstance(result_dca, pd.DataFrame)",
        "assert {'total_cost', 'total_shares', 'portfolio_value', 'return'}.issubset(result_dca.columns)",
        "assert result_dca['total_cost'].iloc[-1] == 1000 * len(result_dca)",
        "assert 'signal' in result.columns",
        "assert result['signal'].dtype == bool",
        "assert len(scan_df) == 24",
        "assert scan_df['ma_period'].min() == 5",
        "assert scan_df['ma_period'].max() == 120",
        "assert len(train) + len(test) == len(df)",
        "assert train.index[-1] < test.index[0]",
        "assert 0.55 < len(train) / len(df) < 0.65",
    ]
    for assertion in required_assertions:
        assert assertion in code
