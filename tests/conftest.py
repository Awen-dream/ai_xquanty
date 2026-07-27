from pathlib import Path

import pytest

from ai_xquanty.config import BacktestConfig
from ai_xquanty.data.loaders import load_market_data


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


@pytest.fixture
def sample_bundle(repo_root):
    return load_market_data(BacktestConfig.from_sample_data(repo_root))
