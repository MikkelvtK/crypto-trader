from decorators import *


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
