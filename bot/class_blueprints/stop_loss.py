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
        self.__highest = None
        self.__trail = None
        self.__open = True

    # ----- CLASS METHODS ----- #

    def adjust_stop_loss(self, price):
        """Adjust current highest point of the trailing stop loss if needed."""
        if price > self.__highest:
            self.__highest = price
            self.__trail = self.__highest * 0.95
            self.__to_sql(update=True)

    def close_stop_loss(self):
        self.__open = False
        self.__to_sql(update=True)

    def __to_sql(self, update=False):
        """Save a newly activated trailing stop loss"""
        session = sessionmaker(self.__engine)

        with session() as connection:
            if update:
                stop_loss = connection.query(StopLoss).get(self.__index)
                stop_loss.highest = self.__highest
                stop_loss.trail = self.__trail
                stop_loss.open_stop_loss = self.__open

            else:
                new_stop_loss = StopLoss(
                    strategy_name=self.__strategy_name,
                    asset=self.__asset,
                    highest=self.__highest,
                    trail=self.__trail,
                    open_stop_loss=self.__open
                )

                connection.add(new_stop_loss)
                self.__index = new_stop_loss.index

            connection.commit()

    def initialise(self, strategy_name, symbol, price):
        self.__strategy_name = strategy_name
        self.__asset = symbol
        self.__highest = price
        self.__trail = self.__highest * 0.95

    def load(self):
        session = sessionmaker(self.__engine)

        try:
            with session() as connection:
                result = connection.query(StopLoss).filter_by(asset=self.__asset, open=True).first()
                self.__index = result.index
                self.__strategy_name = result.strategy_name
                self.__asset = result.asset
                self.__highest = result.highest
                self.__trail = result.trail
        except AttributeError:
            print("There is no active trailing stop loss. Open for business.")

    def query(self):
        session = sessionmaker(self.__engine)

        with session() as connection:
            return connection.query(StopLoss).filter_by(index=self.__index).first()
