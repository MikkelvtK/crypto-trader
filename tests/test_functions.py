from functions import calc_correct_quantity


def test_true_order_quantity(test_bot):
    assert calc_correct_quantity(test_bot.get_step_size("BTCUSDT"), 2.402962145667) == 2.402962
    assert calc_correct_quantity(test_bot.get_step_size("ETHUSDT"), 94.776283266) == 94.77628
    assert calc_correct_quantity(test_bot.get_step_size("BNBUSDT"), 329.6250000) == 329.62
