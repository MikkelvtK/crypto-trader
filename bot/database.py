from sqlalchemy import create_engine
from sqlalchemy import Column, String, Integer, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import config

Base = declarative_base()


class StopLoss(Base):
    __tablename__ = "stop_losses"
    index = Column(Integer, primary_key=True)
    strategy_name = Column(String(250), nullable=False)
    asset = Column(String(250), nullable=False)
    highest = Column(Float, nullable=False)
    trail = Column(Float, nullable=False)


class OrderRecord(Base):
    __tablename__ = "orders"
    order_id = Column(Integer, primary_key=True)
    symbol = Column(String(250), nullable=False)
    crypto_price = Column(Float, nullable=False)
    fiat_value = Column(Float, nullable=False)
    crypto_coins = Column(Float, nullable=False)
    side = Column(String(250), nullable=False)
    order_type = Column(String(250), nullable=False)
    time = Column(Integer, nullable=False)
    status = Column(String(250), nullable=False)
    trade_id = Column(Integer, ForeignKey("trades.trade_id"))
    trade = relationship("Trade")


class Trade(Base):
    __tablename__ = "trades"
    trade_id = Column(Integer, primary_key=True)
    symbol = Column(String(250), nullable=False)
    buy_order_id = Column(Integer, nullable=False)
    sell_order_id = Column(Integer, nullable=True)
    open = Column(Boolean, nullable=False)
    stop_loss_id = Column(Integer, ForeignKey("stop_losses.index"), nullable=True)
    stop_loss = relationship("StopLoss")


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
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
