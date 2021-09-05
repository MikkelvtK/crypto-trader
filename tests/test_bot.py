from decorators import *


@timer_decorator
def test_data(test_bot, ma1, ma2, std):
    df = test_bot.retrieve_usable_data("ETHUSDT", test_bot.strategies[0])
    assert df.shape == (200, 8)
    assert df["Price"].iloc[ma2 - ma1:].sum() / ma1 == df[f"SMA_{ma1}"].iloc[-1]
