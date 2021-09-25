class TrailingStopLoss:

    def __init__(self, strategy_name, asset_symbol, current_price):
        self.strategy_name = strategy_name
        self.asset = asset_symbol
        self.highest = current_price
        self.trail = self.calculate_stop_loss()

    def adjust_stop_loss(self, price):
        """Adjust current highest point of the trailing stop loss if needed."""
        if price > self.highest:
            self.highest = price
            self.trail = self.calculate_stop_loss()

    def calculate_stop_loss(self):
        return self.highest * 0.95

    def log_stop_loss(self, stop_loss):
        """Save a newly activated trailing stop loss"""
        with self.session() as new_session:
            new_stop_loss = StopLoss(
                strategy_name=stop_loss.strategy_name,
                asset=stop_loss.asset,
                highest=stop_loss.highest,
                trail=stop_loss.trail
            )

            new_session.add(new_stop_loss)
            new_session.commit()

    def update_stop_loss(self, stop_loss):
        """Update any changes to the trailing stop loss in the database"""
        metadata = sqlalchemy.MetaData()
        table = sqlalchemy.Table("stop_losses", metadata, autoload_with=self.engine)

        db_update = sqlalchemy.update(table).where(table.columns.strategy_name == stop_loss.strategy_name,
                                                   table.columns.asset == stop_loss.asset).\
            values(highest=stop_loss.highest, trail=stop_loss.trail)

        with self.engine.connect() as connection:
            connection.execute(db_update)

    def delete_stop_loss(self, stop_loss):
        """Delete trailing stop loss if asset is sold"""
        metadata = sqlalchemy.MetaData()
        table = sqlalchemy.Table("stop_losses", metadata, autoload_with=self.engine)
        action_to_execute = table.delete().where(table.columns.strategy_name == stop_loss.strategy_name,
                                                 table.columns.asset == stop_loss.asset)
        with self.engine.connect() as connection:
            connection.execute(action_to_execute)