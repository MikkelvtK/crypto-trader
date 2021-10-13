from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import StopLoss
import config


class TrailingStopLoss:

    def __init__(self):
        self.__engine = create_engine(f"sqlite:///{config.db_path}")
        self.__index = None
        self.__strategy_name = None
        self.__asset = None
        self._buy_price = None
        self.__highest = None
        self._trail = None
        self.__open = True

    @property
    def buy_price(self):
        return self._buy_price

    @property
    def trail(self):
        return self._trail

    # ----- CLASS METHODS ----- #

    def adjust_stop_loss(self, price):
        """Adjust current highest point of the trailing stop loss if needed."""
        if price > self.__highest:
            self.__highest = price
            self._trail = self.__highest * 0.975
            self.__to_sql(update=True)

    def close_stop_loss(self):
        self.__open = False
        self.__to_sql(update=True)

    def __to_sql(self, update=False):
        """Save a newly activated trailing stop loss"""
        session = sessionmaker(self.__engine)

        with session() as connection:
            if update:
                stop_loss = connection.query(StopLoss).filter_by(asset=self.__asset, open_stop_loss=True).first()
                stop_loss.highest = self.__highest
                stop_loss.trail = self._trail
                stop_loss.open_stop_loss = self.__open

            else:
                new_stop_loss = StopLoss(
                    strategy_name=self.__strategy_name,
                    asset=self.__asset,
                    buy_price=self._buy_price,
                    highest=self.__highest,
                    trail=self._trail,
                    open_stop_loss=self.__open
                )

                connection.add(new_stop_loss)
                self.__index = new_stop_loss.index

            connection.commit()

    def initialise(self, strategy_name, symbol, price):
        self.__strategy_name = strategy_name
        self.__asset = symbol
        self._buy_price = price
        self.__highest = price
        self._trail = self.__highest * 0.975
        self.__to_sql(update=False)

    def load(self, symbol):
        session = sessionmaker(self.__engine)

        with session() as connection:
            result = connection.query(StopLoss).filter_by(asset=symbol, open_stop_loss=True).first()
            self.__index = result.index
            self.__strategy_name = result.strategy_name
            self.__asset = result.asset
            self._buy_price = result.buy_price
            self.__highest = result.highest
            self._trail = result.trail

    def query(self):
        session = sessionmaker(self.__engine)

        with session() as connection:
            return connection.query(StopLoss).filter_by(index=self.__index).first()
