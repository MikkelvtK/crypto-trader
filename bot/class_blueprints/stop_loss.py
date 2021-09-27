from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from bot.database import StopLoss
import bot.config as config


class TrailingStopLoss:

    def __init__(self, strategy_name, symbol, current_price):
        self.__engine = create_engine(f"sqlite:///{config.db_path}")
        self.__index = None
        self.__strategy_name = strategy_name
        self.__asset = symbol
        self.__highest = current_price
        self.__trail = self.__highest * 0.95
        self.__to_sql()

    # ----- CLASS METHODS ----- #

    def adjust_stop_loss(self, price):
        """Adjust current highest point of the trailing stop loss if needed."""
        if price > self.__highest:
            self.__highest = price
            self.__trail = self.__highest * 0.95
            self.__to_sql(update=True)

    def __to_sql(self, update=False):
        """Save a newly activated trailing stop loss"""
        session = sessionmaker(self.__engine)

        with session() as connection:
            if update:
                db_update = {"highest": self.__highest, "trail": self.__trail}
                connection.query(StopLoss).get(self.__index).update(db_update)

            else:
                new_stop_loss = StopLoss(
                    strategy_name=self.__strategy_name,
                    asset=self.__asset,
                    highest=self.__highest,
                    trail=self.__trail
                )

                connection.add(new_stop_loss)
                self.__index = new_stop_loss.index

            connection.commit()

    def query(self):
        session = sessionmaker(self.__engine)

        with session() as connection:
            return connection.query(StopLoss).filter_by(index=self.__index).first()
