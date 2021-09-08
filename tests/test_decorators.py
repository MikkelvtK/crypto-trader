import pytest


def test_crash_email(test_trader):
    with pytest.raises(SystemExit):
        data = test_trader.get_history(symbol="ethusdt", interval="4h", limit=10)
