import math
from sqlalchemy.orm import sessionmaker
from bot.database import OrderRecord, Trade


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

    def to_sql(self, engine, buy_order_id=None):
        session = sessionmaker(engine)

        with session() as connection:
            if self.side == "buy":
                trade = Trade(
                    buy_order_id=self._id,
                    sell_order_id=0,
                    open=True
                )
                connection.add(trade)

            else:
                db_update = {"sell_order_id": self._id, "open": False}
                connection.query(Trade).filter_by(buy_order_id=buy_order_id).update(db_update)
                trade = connection.query(Trade).filter_by(buy_order_id=buy_order_id).first()

            new_order = OrderRecord(
                order_id=self._id,
                symbol=self.symbol,
                crypto_price=self.price,
                fiat_value=self.investment,
                crypto_coins=self._coins,
                side=self.side,
                order_type=self.type,
                time=self._time,
                status=self._status,
            )

            new_order.trade = trade
            connection.add(new_order)
            connection.commit()

#TODO 1: Create query method for orders and trades
#TODO 2: Create method to return if trade is open (bool result)
