from trader import TraderAPI
from candlestick import Candlestick
import datetime as dt
from functions import *
import time
from config import *
from sqlalchemy.orm import sessionmaker
import sqlalchemy
from database import *



def log_candlestick(candlestick_to_log):
    new_engine = sqlalchemy.create_engine("sqlite:///../data/trades.db")
    session = sessionmaker(new_engine)

    with session() as new_session:
        new_candlestick = CandlestickDatabase(
            interval=candlestick_to_log.interval,
            symbol=candlestick_to_log.symbol,
            open_time=candlestick_to_log.open_time,
            open_price=candlestick_to_log.open_price,
            high=candlestick_to_log.high,
            low=candlestick_to_log.low,
            close_price=candlestick_to_log.close_price,
            close_time=candlestick_to_log.close_time
        )
        new_session.add(new_candlestick)
        new_session.commit()


def update_candlestick(candlestick_to_update):
    new_engine = sqlalchemy.create_engine("sqlite:///../data/trades.db")
    metadata = sqlalchemy.MetaData()
    table = sqlalchemy.Table("candlesticks", metadata, autoload_with=new_engine)

    db_update = sqlalchemy.update(table).where(table.columns.interval == candlestick_to_update.interval,
                                               table.columns.symbol == candlestick_to_update.symbol,
                                               table.columns.open_time == candlestick_to_update.open_time).\
        values(high=candlestick_to_update.high, low=candlestick_to_update.low,
               close_price=candlestick_to_update.close_price)

    with new_engine.connect() as connection:
        connection.execute(db_update)


def clear_database():
    new_engine = sqlalchemy.create_engine("sqlite:///../data/trades.db")

    entries_to_delete = sqlalchemy.delete(CandlestickDatabase).where()

    with new_engine.connect() as connection:
        connection.execute(entries_to_delete)


clear_database()
api = TraderAPI()

new_data = api.get_history(symbol="VETEUR", interval="5m", limit=M5[1])



current_time = time.time()



