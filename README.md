# Crypto Trading Bot

A bot that uses the Binance API to place trade orders using predefined strategies.

## Description

The bot uses a combination of strategies to place trade orders on assets using the Binance Api.

The strategies used are:
* Crossing moving averages (MA). MA1 is calculated over 40 intervals and MA2 is calculated over 170 intervals. 
  The interval is 4 hours.
* RSI dips. When the RSI dips below 30 the bot will place a buy order and hold it until the RSI is back to 40 
  or when 5 intervals have passed. Whichever comes first. The interval used is 1 hour.
* Bollinger Bands. When the price drops below the lower Bollinger band, and the RSI is below 30 the bot will place a buy order.
  The asset sells when the price reaches the upper Bollinger band or when the trailing stop loss triggers. 

## Getting Started

### Dependencies

* All you need to have installed is Python 3.9.5+. The requirements.txt file will install any necessary libraries in order to run the script.

### Installing

The project will mostly run out of the box. Just a few things need to be done.

* Clone the project.
* Create a config.py
* To the config.py add:
  * Binance API and secret
  * Command to restart bot
  * path to databases
```
command = your_command_to_restart
apiKey = your_api_key
apiSecret = your_api_secret
db_path = your_database_path
```

* Change the assets you want to trade in main.py if you want.
* If you want to leave out any strategy you can remove them from the tuple in main.py:
```
strategies = (crossing_sma, bottom_rsi, bollinger)
```

### Newest Release:

* Overhauls the financial management system
* Moves the bot to his own class

### Under Development:

* Any bug fixes that may arise during testing
* Adding a notification system when trade orders have been placed.
* A weekly summary displaying how the bot has performed.

