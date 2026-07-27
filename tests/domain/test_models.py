from datetime import date

import pytest

from ai_xquanty.domain.models import Instrument


def test_instrument_rejects_unsupported_type() -> None:
    with pytest.raises(ValueError, match="ETF-only"):
        Instrument(
            symbol="600000.SH",
            market="SSE",
            instrument_type="STOCK",
            list_date=date(2020, 1, 1),
            is_active=True,
        )
