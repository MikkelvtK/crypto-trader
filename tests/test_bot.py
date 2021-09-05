from decorators import *


@timer_decorator
def test_data(test_bot):
    df = test_bot.retrieve_usable_data("ETHUSDT", test_bot.strategies[0])
    assert df.shape == (200, 8)
