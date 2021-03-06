from functions import format_border
from class_blueprints.trader import get_balance
import psutil


class Portfolio:

    def __init__(self, owner, fiat, cryptos):
        self._owner = owner
        self._fiat = fiat
        self._fiat_balance = 0
        self._crypto_balances = {crypto.get_symbol(): crypto for crypto in cryptos}
        self.update_portfolio()

    # ----- GETTERS / SETTERS ----- #

    @property
    def owner(self):
        return self._owner

    @property
    def fiat(self):
        return self._fiat

    @property
    def fiat_balance(self):
        return self._fiat_balance

    @fiat_balance.setter
    def fiat_balance(self, new_fiat_balance):
        if new_fiat_balance < 0:
            raise Exception("Fiat balance cannot be negative.")
        else:
            self._fiat_balance = new_fiat_balance

    @property
    def crypto_balances(self):
        return self._crypto_balances

    # ----- CLASS METHODS ----- #

    def update_portfolio(self):
        """
        Updates all the crypto balances in the portfolio.
        """

        data = get_balance()

        for balance in data["balances"]:
            if balance["asset"].lower() == self._fiat:
                self._fiat_balance = float(balance["free"])

        for symbol, crypto in self._crypto_balances.items():
            crypto.update_balance(data=data)

    def query_crypto_balance(self, crypto):
        """
        Queries portfolio and returns the crypto object that was requested.

        :param crypto: (str) The asset that is requested.
        :return: (object) Crypto object.
        """

        return self._crypto_balances[crypto]

    def get_active_balances_count(self, price):
        """
        Returns the number of balances in the portfolio that have a substantial amount of coins.

        :param price: (float) The latest price of the asset.
        :return: (int) Returns number of active balances.
        """

        k = 0
        for symbol, crypto in self._crypto_balances.items():
            if crypto.balance * price > 10:
                k += 1
        return k

    def print_portfolio(self):
        """
        Prints the the information of the user's portfolio.
        """

        format_border(f"PORTFOLIO {self._owner.upper()}")
        print(f"\nCurrent fiat balance: {round(self._fiat_balance, 2)} {self._fiat.upper()}.")

        for symbol, crypto in self._crypto_balances.items():
            print(f"Current {crypto.name.title()} balance: {crypto.balance}.")

        print(f"Current CPU usage: {psutil.cpu_percent(4)}.\n")
