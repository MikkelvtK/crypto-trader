from sqlalchemy.orm import sessionmaker
from database import CryptoBalance


class Crypto:

    __NEGATIVE = "Number cannot be negative."

    def __init__(self, crypto, fiat):
        self._crypto = crypto
        self.__fiat = fiat
        self._balance = 0

    # ----- GETTERS / SETTERS ----- #

    @property
    def crypto(self):
        return self._crypto

    @property
    def balance(self):
        return self._balance

    @balance.setter
    def balance(self, new_balance):
        if new_balance < 0:
            raise Exception(self.__NEGATIVE)
        self._balance = new_balance

    # ----- CLASS METHODS ----- #

    def get_symbol(self):
        return self._crypto + self.__fiat
