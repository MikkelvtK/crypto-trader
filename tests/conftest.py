from trader import TraderAPI
from strategies import *
from bot import TraderBot
from constants import *
from sqlalchemy.ext.declarative import declarative_base
import pytest
from decorators import *


@pytest.fixture
def test_trader():
    trader = TraderAPI()
    trader.key = config.testApiKey
    trader.secret = config.testApiSecret
    trader.header = {"X-MBX-APIKEY": trader.key}
    trader.endpoint = "https://testnet.binance.vision"
    return trader


@pytest.fixture
def test_bot(test_trader):
    crossing_sma = CrossingSMA(MA1, MA2, interval=H4, assets=[], name="test")
    bottom_rsi = BottomRSI(interval=H1, assets=[], name="test")
    bollinger = BollingerBands(interval=M30, assets=[], name="test")
    strategies = (crossing_sma, bottom_rsi, bollinger)
    return TraderBot("test", test_trader, strategies, "usdt")


@pytest.fixture
def bot_budget(test_bot):
    test_bot.total_budget = 1000
    test_bot.current_balance = 175
    data = {"asset": ["btcusdt", "btcusdt"], "type": ["long", "short"], "investment": [650, 175]}
    test_bot.active_investments = pd.DataFrame(data)
    return test_bot


@pytest.fixture
def test_trade_log():
    return declarative_base()
