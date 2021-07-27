# Crypto Trading Bot

A bot that uses the Binance API to place trade orders using predefined strategies.

## Description

The bot uses a combination of strategies to place trade orders on assets using the Binance Api.

The strategies used are:
* Crossing moving averages (MA). MA1 is calculated over 40 intervals and MA2 is calculated over 170 intervals. 
  The interval is set to 4 hour.
* RSI dips. When the RSI dips below 30 the bot will place a buy order and hold it until the RSI is back to 40 
  or when 5 intervals have passed. Whichever comes first. The interval used is 1 hour.
* Bollinger Bands. When the price drops below the lower Bollinger band and the RSI is below 30 the bot will place a buy order.
  The asset is sold when the price reaches the upper Bollinger band or when the trailing stop loss is activated. 

## Getting Started

### Dependencies

* All you need to have installed is Python 3.9.5+. The requirements.txt file will install any necessary libraries in order to run the script.

### Installing

The project will mostly run out of the box. Just a few things need to be done.

* Clone the project.
* Add your Binance API key and secret to the environment variables.
* Change the assets you want to trade in the wallet.py file.
* If you want to leave out any strategy you can remove them from the tuple in main.py:
```
strategies = (crossing_sma, bottom_rsi, bollinger)
```

## Version History

* 0.1
    * Initial Release
  
### Under Development:

* Adding a notification system when trade orders have been placed.
* A weekly summary displaying how the bot has performed.
* A database logging trades
* Any bug fixes that may arise
