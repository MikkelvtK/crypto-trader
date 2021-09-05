from trader import TraderAPI
from strategies import *
from bot import TraderBot
from constants import *
import pytest


@pytest.fixture
def test_bot():
    trader = TraderAPI()
    crossing_sma = CrossingSMA(MA1, MA2, interval=H4, assets=[], name="test")
    bottom_rsi = BottomRSI(interval=H1, assets=[], name="test")
    bollinger = BollingerBands(interval=M30, assets=[], name="test")
    strategies = (crossing_sma, bottom_rsi, bollinger)
    return TraderBot("test", trader, strategies)
