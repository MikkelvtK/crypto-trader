from sqlalchemy.orm import sessionmaker
from database import OrderRecord, Trade


class Order:

    def __init__(self, **kwargs):
        self._id = kwargs["order_id"]
        self._symbol = kwargs["symbol"]
        self._price = kwargs["price"]
        self._investment = kwargs["investment"]
        self._coins = kwargs["coins"]
        self._side = kwargs["side"]
        self._type = kwargs["type"]
        self._time = kwargs["time"]
        self._status = kwargs["status"]

    # ----- GETTERS / SETTERS ----- #

    @property
    def id(self):
        return self._id

    @property
    def symbol(self):
        return self._symbol

    @property
    def price(self):
        return self._price

    @property
    def investment(self):
        return self._investment

    @property
    def coins(self):
        return self._coins

    @property
    def side(self):
        return self._side

    @property
    def type(self):
        return self._type

    @property
    def time(self):
        return self._time

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, order_status):
        self._status = order_status.lower()

    # ----- CLASS METHODS ----- #

    def to_sql(self, engine, buy_order_id=None, stop_loss=None):
        if self._side == "sell" and buy_order_id is None:
            raise Exception("A sell order cannot be logged without a buy_order_id from the corresponding buy_order.")

        session = sessionmaker(engine)

        with session() as connection:
            if self._side == "buy":
                trade = Trade(
                    symbol=self._symbol,
                    buy_order_id=self._id,
                    sell_order_id=0,
                    open=True
                )

                if stop_loss:
                    trade.stop_loss = stop_loss

                connection.add(trade)

            else:
                db_update = {"sell_order_id": self._id, "open": False}
                connection.query(Trade).filter_by(buy_order_id=buy_order_id).update(db_update)
                trade = connection.query(Trade).filter_by(buy_order_id=buy_order_id).first()

            new_order = OrderRecord(
                order_id=self._id,
                symbol=self._symbol,
                crypto_price=self._price,
                fiat_value=self._investment,
                crypto_coins=self._coins,
                side=self._side,
                order_type=self._type,
                time=self._time,
                status=self._status,
            )

            new_order.trade = trade
            connection.add(new_order)
            connection.commit()

    def get_last_buy_order(self, engine):
        session = sessionmaker(engine)

        try:
            with session() as connection:
                buy_orders = connection.query(OrderRecord).filter_by(symbol=self._symbol, side="buy")
                return buy_orders[-1]

        except IndexError:
            print("No previous order found. Database must have been reset.")
