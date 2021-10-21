from sqlalchemy import create_engine
from sqlalchemy import Column, String, Integer, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
import config

Base = declarative_base()


class StopLoss(Base):
    __tablename__ = "stop_losses"
    index = Column(Integer, primary_key=True)
    strategy_name = Column(String(250), nullable=False)
    asset = Column(String(250), nullable=False)
    buy_price = Column(Float, nullable=False)
    highest = Column(Float, nullable=False)
    trail_ratio = Column(Float, nullable=False)
    trail = Column(Float, nullable=False)
    open_stop_loss = Column(Boolean, nullable=False)


if __name__ == "__main__":

    # Create database and connection
    engine = create_engine(f"sqlite:///{config.db_path}")
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
