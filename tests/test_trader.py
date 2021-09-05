def test_sell_order(test_trader):
    print(test_trader.post_order(asset="BTCUSDT", quantity=1, manner="quantity", action="SELL"))
