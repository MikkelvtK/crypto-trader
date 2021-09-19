import pytest
from bot.decorators import *


@timer_decorator
def test_available_budget(bot_budget):
    available_budget = bot_budget.calculate_available_budget()
    assert available_budget["available day trading budget"] == 175
    assert available_budget["available hodl budget"] == 0


@timer_decorator
def test_reading_active_stop_losses(bot_stop_loss):
    bot_stop_loss.set_active_stop_losses()
    assert bot_stop_loss.active_stop_losses["RSI Dips"]["ethusdt"].highest == 3000
    assert bot_stop_loss.active_stop_losses["Bol Bands"]["ethusdt"].trail == 2850


@timer_decorator
def test_analysing_data(dataset1, dataset2):
    bot2 = dataset2[0]
    action1 = dataset1[0].analyse_new_data(dataset1[1], "ETHUSDT", dataset1[0].strategies[0])
    action2 = dataset2[0].analyse_new_data(dataset2[1], "ETHUSDT", dataset2[0].strategies[2])
    assert action1 == "buy"
    assert bot2.active_stop_losses[bot2.strategies[2].name]["ETHUSDT"].trail == dataset2[1]["Price"].iloc[-1] * 0.95
    assert action2 is None


@timer_decorator
def test_determine_investment_amount(bot_budget):
    bot_budget.available_to_invest = bot_budget.calculate_available_budget()
    investment_hodl = bot_budget.determine_investment_amount(bot_budget.strategies[0])
    investment_rsi = bot_budget.determine_investment_amount(bot_budget.strategies[1])
    assert investment_rsi == 175
    assert investment_hodl is None


@timer_decorator
def test_prepare_order(bot_budget):
    bot_budget.available_to_invest = bot_budget.calculate_available_budget()
    investment = bot_budget.prepare_order("btcusdt", bot_budget.strategies[1], "buy")
    sell_quantity = bot_budget.prepare_order("btcusdt", bot_budget.strategies[0], "sell")
    do_nothing = bot_budget.prepare_order("btcusdt", bot_budget.strategies[0], None)
    assert investment == 175
    assert sell_quantity == 1
    assert do_nothing is None


# @timer_decorator
# def test_place_order(test_bot):
#     receipt = test_bot.place_order("BTCUSDT", 5000, "buy")
#     r
#     assert receipt["status"].lower() == "filled"


@timer_decorator
def test_removing_stop_losses(dataset2):
    bot = dataset2[0]
    del bot.active_stop_losses["Bol Bands"]["BTCUSDT"]
    with pytest.raises(KeyError):
        print(bot.active_stop_losses["Bol Bands"]["BTCUSDT"])
    assert isinstance(bot.active_stop_losses["Bol Bands"]["ETHUSDT"], object) is True


@timer_decorator
def test_place_limit_order(test_bot):
    receipt = test_bot.place_limit_order(asset_symbol="ethusdt", order_quantity=100, action="buy")
    print(receipt)
    assert receipt["status"] == "FILLED"
