import json
from pathlib import Path


def _load_notebook() -> dict:
    notebook_path = Path("docs/superpowers/specs/course/q7-execution/notebooks/q7-execution.ipynb")
    return json.loads(notebook_path.read_text(encoding="utf-8"))


def _cell_source(cell: dict) -> str:
    source = cell.get("source", "")
    if isinstance(source, list):
        return "".join(source)
    return source


def _code() -> str:
    notebook = _load_notebook()
    return "\n".join(
        _cell_source(cell)
        for cell in notebook["cells"]
        if cell.get("cell_type") == "code"
    )


def test_q7_notebook_code_cells_compile() -> None:
    notebook = _load_notebook()
    for index, cell in enumerate(notebook["cells"]):
        if cell.get("cell_type") != "code":
            continue
        compile(_cell_source(cell), f"q7-cell-{index}", "exec")


def test_q7_notebook_uses_stable_paths_for_data_and_images() -> None:
    code = _code()
    assert "def find_repo_root()" in code
    assert "ROOT = find_repo_root()" in code
    assert 'DATA_DIR = ROOT / "data" / "oxq" / "market"' in code
    assert 'IMAGE_DIR = Q7_DIR / "book" / "images"' in code
    assert "IMAGE_DIR.mkdir(parents=True, exist_ok=True)" in code
    assert 'plt.savefig("../book/images/' not in code
    assert "LocalMarketDataProvider()" not in code
    assert "LocalMarketDataProvider(data_dir=DATA_DIR)" in code
    assert "dest_dir=DATA_DIR" in code


def test_q7_notebook_declares_alpaca_import_as_optional() -> None:
    code = _code()
    assert "try:" in code
    assert "from oxq.contrib.alpaca import AlpacaClient, AlpacaMarketDataProvider" in code
    assert "except ImportError as e:" in code
    assert "Alpaca 可选依赖未安装" in code
