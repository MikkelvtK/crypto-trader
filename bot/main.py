import config
from class_blueprints.strategies import Strategy
from class_blueprints.crypto import Crypto
from class_blueprints.portfolio import Portfolio
from trader_bot import TraderBot


def main():

    # Create all objects
    cryptos = [Crypto(crypto=key, fiat=config.FIAT_MARKET, name=value) for key, value in config.CRYPTOS.items()]
    portfolio = Portfolio(owner=config.USER, fiat=config.FIAT_MARKET, cryptos=cryptos)

    strategies = []
    for symbol, crypto in portfolio.crypto_balances.items():
        strategy = Strategy(symbol=symbol, name="Golden Cross", crypto=crypto)
        strategies.append(strategy)

    # Create bot object and activate it
    bot = TraderBot(name=config.BOT_NAME, strategies=strategies, portfolio=portfolio)
    bot.activate()


if __name__ == "__main__":
    main()
