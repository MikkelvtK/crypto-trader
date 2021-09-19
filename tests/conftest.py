from bot.class_blueprints.trader import TraderAPI
from bot.class_blueprints.strategies import *
from bot import TraderBot
from bot.constants import *
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest
from bot.decorators import *


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
    crossing_sma = CrossingSMA(MA1, MA2, interval=H4, assets=[], name="Golden Cross")
    bottom_rsi = BottomRSI(interval=H1, assets=[], name="RSI Dips")
    bollinger = BollingerBands(interval=M30, assets=[], name="Bol Bands")
    strategies = (crossing_sma, bottom_rsi, bollinger)
    return TraderBot("test", test_trader, strategies, "usdt")


@pytest.fixture
def bot_budget(test_bot):
    test_bot.total_budget = 1000
    test_bot.current_balance = 175
    data = {"asset": ["btcusdt", "btcusdt"], "type": ["long", "short"], "investment": [650, 175],
            "coins": [1, 0.5], "strategy": ["Golden Cross", "RSI Dips"]}
    test_bot.active_investments = pd.DataFrame(data)
    return test_bot


@pytest.fixture
def bot_stop_loss(test_bot):
    test_bot.engine = create_engine(f"sqlite:///tests/data/trades.db")
    test_bot.session = sessionmaker(test_bot.engine)
    return test_bot


@pytest.fixture
def dataset1(test_bot):
    data = test_bot.retrieve_usable_data("ETHUSDT", test_bot.strategies[0])
    data[f"SMA_{MA1}"] = data[f"SMA_{MA1}"].replace([data[f"SMA_{MA1}"].iloc[-1]], 2000)
    data[f"SMA_{MA2}"] = data[f"SMA_{MA2}"].replace([data[f"SMA_{MA2}"].iloc[-1]], 1500)
    return test_bot, data


@pytest.fixture
def dataset2(test_bot):
    bol_strategy = test_bot.strategies[2]
    asset = "ETHUSDT"
    data = test_bot.retrieve_usable_data(asset, bol_strategy)
    stop_loss = TrailingStopLoss(bol_strategy.name, asset, 300)
    stop_loss2 = TrailingStopLoss(bol_strategy.name, "BTCUSDT", 30000)
    test_bot.active_stop_losses[stop_loss.strategy_name][stop_loss.asset] = stop_loss
    test_bot.active_stop_losses[stop_loss2.strategy_name][stop_loss2.asset] = stop_loss2
    test_bot.active_investments = pd.DataFrame({"asset": [asset, "BTCUSDT"],
                                                "strategy": [bol_strategy.name, bol_strategy.name]})
    return test_bot, data
