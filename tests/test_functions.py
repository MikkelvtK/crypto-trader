from functions import calc_correct_quantity


def test_true_order_quantity():
    assert calc_correct_quantity(2, 2046.40296000) == 2046.40
    assert calc_correct_quantity(1, 94.77628000) == 94.7
    assert calc_correct_quantity(-1, 329.6250000) == 329
    assert calc_correct_quantity(2, 5.2732526) == 5.27
