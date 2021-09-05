from functions import calc_correct_quantity


def test_true_order_quantity(test_bot):
    assert calc_correct_quantity(test_bot.get_step_size("VETEUR"), 2046.40296000) == 2046.40
    assert calc_correct_quantity(test_bot.get_step_size("ADAEUR"), 94.77628000) == 94.7
    assert calc_correct_quantity(test_bot.get_step_size("DOGEEUR"), 329.6250000) == 329
    assert calc_correct_quantity(test_bot.get_step_size("LINKEUR"), 5.2732526) == 5.27
    assert calc_correct_quantity(test_bot.get_step_size("HOTEUR"), 2046.40296000) == 2046.4
