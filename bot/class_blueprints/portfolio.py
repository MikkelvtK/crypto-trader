from crypto import Crypto


class Portfolio:

    def __init__(self, owner, fiat, fiat_balance, hodl_crypto, cryptos):
        self._owner = owner
        self._fiat = fiat
        if fiat_balance < 0:
            raise Exception("Fiat balance cannot be negative.")
        else:
            self._fiat_balance = fiat_balance
        self._hodl_crypto = hodl_crypto
        self._crypto_balances = {crypto: Crypto(crypto, fiat).from_sql() for crypto in cryptos}

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
    def hodl_crypto(self):
        return self._hodl_crypto

    @property
    def crypto_balances(self):
        return self._crypto_balances

    def query_crypto_balance(self, crypto):
        return self._crypto_balances[crypto]
