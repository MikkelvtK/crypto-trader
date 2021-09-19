class Order:

    def __init__(self, receipt, price, investment):
        self.id = receipt["orderId"]
        self.symbol = receipt["symbol"].lower()
        self.price = price
        self.coins = receipt["executedQty"]
        self.investment = investment
        self.side = receipt["side"].lower()
        self.type = receipt["type"].lower()
        self.time = receipt["transactTime"]
        self.status = receipt["status"].lower()

    def update_status(self, query_result):
        self.status = query_result["status"].lower()
