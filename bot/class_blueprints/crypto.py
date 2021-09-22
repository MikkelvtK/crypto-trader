class Crypto:

    __NEGATIVE = "Number cannot be negative."
    __NO_INVESTMENT = "There has not been invested in this crypto currency."

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
        if new_investment < 0:
            raise Exception(self.__NEGATIVE)
        self._investment = new_investment

    @property
    def balance(self):
        return self._balance

    @balance.setter
    def balance(self, new_balance):
        if new_balance < 0:
            raise Exception(self.__NEGATIVE)
        self._balance = new_balance

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, current_price):
        if self.investment <= 0:
            raise Exception(self.__NO_INVESTMENT)
        self._value = self.balance * current_price

    def get_profit(self):
        if self.investment <= 0:
            raise Exception(self.__NO_INVESTMENT)
        return self.value - self.investment

    def get_profit_ratio(self):
        if self.investment <= 0:
            raise Exception(self.__NO_INVESTMENT)
        return (self.value - self.investment) / self.investment * 100

    def get_symbol(self):
        return self.__crypto + self.__fiat

    def buy(self):
        pass

    def sell(self):
        pass

    def to_sql(self):
        pass

    def from_sql(self):
        pass
