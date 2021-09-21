class Crypto:

    __NEGATIVE = "Number cannot be negative."

    def __init__(self, crypto, fiat):
        self.__crypto = crypto
        self.__fiat = fiat
        self._investment = 0
        self._balance = 0
        self._value = 0

    @property
    def investment(self):
        return self._investment

    @investment.setter
    def investment(self, new_investment):
        if self._balance < 0:
            raise Exception(self.__NEGATIVE)
        self._investment = new_investment

    @property
    def balance(self):
        return self._balance

    @balance.setter
    def balance(self, new_balance):
        if self._balance < 0:
            raise Exception(self.__NEGATIVE)
        self._balance = new_balance

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, current_price):
        self._value = self.balance * current_price

    def get_profit(self):
        return self.value - self.investment

    def get_profit_ratio(self):
        return (self.value - self.investment) / self.investment

    def get_symbol(self):
        return self.__crypto + self.__fiat
