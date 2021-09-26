import config
from sqlalchemy import create_engine
from class_blueprints.strategies import Strategy
from class_blueprints.crypto import Crypto
from trader_bot import TraderBot


def main():
    engine = create_engine(f"sqlite:///{config.db_path}")

    # Create all objects
    cryptos = [Crypto(crypto, config.FIAT_MARKET) for crypto in config.CRYPTOS]

    strategies = []
    for crypto in cryptos:
        crypto.from_sql(engine=engine)
        symbol = crypto.get_symbol()
        strategy = Strategy(symbol=symbol, name="Golden Cross")
        strategies.append(strategy)

    # Create bot object and activate it
    bot = TraderBot(name=config.BOT_NAME, strategies=strategies, cryptos=cryptos)
    bot.activate()


if __name__ == "__main__":
    main()
