class Portfolio:

    def __init__(self, owner, fiat, cryptos):
        self._owner = owner
        self._fiat = fiat
        self._fiat_balance = 0
        self._crypto_balances = {crypto.get_symbol(): crypto for crypto in cryptos}

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

    def query_crypto_balance(self, crypto):
        return self._crypto_balances[crypto]

    def get_active_balances_count(self):
        k = 0

        for symbol, crypto in self._crypto_balances.items():
            if crypto.balance > 0:
                k += 1

        return k

