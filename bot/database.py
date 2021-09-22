from sqlalchemy import create_engine
from sqlalchemy import Column, String, Integer, Float
from sqlalchemy.ext.declarative import declarative_base
import config

Base = declarative_base()


class TradeLog(Base):
    __tablename__ = "active_trades"
    index = Column(Integer, primary_key=True)
    asset = Column(String(250), nullable=False)
    coins = Column(Float, nullable=False)
    investment = Column(Float, nullable=False)
    strategy = Column(String(250), nullable=False)
    type = Column(String(250), nullable=False)


class StopLoss(Base):
    __tablename__ = "stop_losses"
    index = Column(Integer, primary_key=True)
    strategy_name = Column(String(250), nullable=False)
    asset = Column(String(250), nullable=False)
    highest = Column(Float, nullable=False)
    trail = Column(Float, nullable=False)


class OrderRecord(Base):
    __tablename__ = "orders"
    index = Column(Integer, primary_key=True)
    order_id = Column(Integer, nullable=False)
    symbol = Column(String(250), nullable=False)
    price = Column(Float, nullable=False)
    investment = Column(Float, nullable=False)
    coins = Column(Float, nullable=False)
    side = Column(String(250), nullable=False)
    order_type = Column(String(250), nullable=False)
    time = Column(Integer, nullable=False)
    status = Column(String(250), nullable=False)


class CryptoBalance(Base):
    __tablename__ = "crypto_balances"
    index = Column(Integer, primary_key=True)
    crypto = Column(String(250), nullable=False)
    fiat = Column(String(250), nullable=False)
    investment = Column(Float, nullable=False)
    balance = Column(Float, nullable=False)
    value = Column(Float, nullable=False)


if __name__ == "__main__":

    # Create database and connection
    engine = create_engine(f"sqlite:///{config.db_path}")
    Base.metadata.create_all(engine)
