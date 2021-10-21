class Crypto:

    __NEGATIVE = "Number cannot be negative."

    def __init__(self, crypto, fiat, name):
        self._crypto = crypto
        self.__fiat = fiat
        self._name = name
        self._balance = 0

    # ----- GETTERS / SETTERS ----- #

    @property
    def crypto(self):
        return self._crypto

    @property
    def name(self):
        return self._name

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
        """Combines the crypto and fiat to return symbol used for trades."""
        return self._crypto + self.__fiat

    def update_balance(self, data):
        """
        Updates the balance of the crypto currently in the user's account.

        :param data: (dict) Takes a response from Account Information endpoint of the Binance API. It will search for
        the crypto in the response and update the class attribute.
        """
        for balance in data["balances"]:
            if balance["asset"].lower() == self._crypto:
                self._balance = float(balance["free"])
