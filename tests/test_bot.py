from decorators import *


@timer_decorator
def test_available_budget(bot_budget):
    available_budget = bot_budget.calculate_available_budget()
    assert available_budget["available day trading budget"] == 175
    assert available_budget["available hodl budget"] == 0
