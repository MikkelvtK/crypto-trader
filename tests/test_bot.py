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
