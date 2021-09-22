import math


class Order:

    __EXCEPTION_MESSAGE = "Order has not been placed yet so no value has been set."

    def __init__(self, symbol, price, investment, side, order_type):
        self._id = None
        self.symbol = symbol
        self.price = price
        self.investment = investment
        self._coins = None
        self.side = side
        self.type = order_type
        self._time = None
        self._status = None

    @property
    def id(self):
        if self._id is None:
            raise Exception(self.__EXCEPTION_MESSAGE)
        return self._id

    @property
    def coins(self):
        if self._id is None:
            raise Exception(self.__EXCEPTION_MESSAGE)
        return self._coins

    @property
    def time(self):
        if self._id is None:
            raise Exception(self.__EXCEPTION_MESSAGE)
        return self._time

    @property
    def status(self):
        if self._id is None:
            raise Exception(self.__EXCEPTION_MESSAGE)
        return self._status

    @status.setter
    def status(self, order_status):
        self._status = order_status.lower()

    def update_order(self, receipt):
        self._id = receipt["orderId"]
        self._coins = float(receipt["executedQty"])
        self._time = math.floor(receipt["transactTime"] / 1000)
        self._status = receipt["status"].lower()

    def to_sql(self):
        pass
