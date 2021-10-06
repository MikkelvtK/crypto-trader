from sqlalchemy.orm import sessionmaker
from database import CryptoBalance


class Crypto:

    __NEGATIVE = "Number cannot be negative."
    __NO_INVESTMENT = "There has not been invested in this crypto currency."

    def __init__(self, crypto, fiat):
        self.__crypto = crypto
        self.__fiat = fiat
        self._investment = 0
        self._balance = 0
        self._value = 0

    # ----- GETTERS / SETTERS ----- #

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

    # ----- CLASS METHODS ----- #

    def get_profit(self):
        if self.investment <= 0:
            return self.__NO_INVESTMENT
        return self.value - self.investment

    def get_profit_ratio(self):
        if self.investment <= 0:
            return self.__NO_INVESTMENT
        return (self.value - self.investment) / self.investment * 100

    def get_symbol(self):
        return self.__crypto + self.__fiat

    def update(self, investment=0, balance=0, value=0):
        self.investment = investment
        self.balance = balance
        self.value = value

    def to_sql(self, engine, update=True):
        session = sessionmaker(engine)

        with session() as con:

            if update:
                update = {"investment": self._investment, "balance": self._balance, "value": self._value}
                con.query(CryptoBalance).filter_by(crypto=self.__crypto, fiat=self.__fiat).update(update)

            else:
                new_update = CryptoBalance(
                    crypto=self.__crypto,
                    fiat=self.__fiat,
                    investment=self._investment,
                    balance=self._balance,
                    value=self._value
                )
                con.add(new_update)

            con.commit()

    def from_sql(self, engine):
        session = sessionmaker(engine)

        try:
            with session() as con:
                result = con.query(CryptoBalance).filter_by(crypto=self.__crypto).first()
                self._investment = result.investment
                self._balance = result.balance
                self._value = result.value
        except AttributeError:
            self.to_sql(engine=engine, update=False)
            print(f"{(self.__crypto + self.__fiat).title()} has not been used and is therefore not in the database. "
                  f"Default numbers will be used.")
