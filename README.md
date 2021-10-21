# Crypto Trading Bot

A bot that uses the Binance API to place trade orders using a predefined strategy.

## Description

The bot uses a crossing EMA with a 4h interval to determine which strategy to use.

* If EMA_50 > EMA200: Will use a trend strategy by using crossing EMA's using fibonacci numbers for the lengths (8 and 21).
* If EMA_50 < EMA200: Will use an RSI dip strategy to catch exceptional opportunities. 
* Uses a trailing stop loss to minimise losses. 

## Getting Started

### Dependencies

* All you need to have installed is Python 3.9.5+. The requirements.txt file will install any necessary libraries in order to run the script.

### Installing

The project will mostly run out of the box. Just a few things need to be done.

* Clone the project.
* Create a config.py
* To the config.py add:
  * Binance API, secret and header
  * Command to restart bot
  * path to databases
  * Settings for the bot

```
FIAT_MARKTET = fiat market you want to use ie. "eur" (lower case).
CRYPTOS = [Crypos, you, want, to, trade] (ie. "btc", "eth")
USER = your_username
BOT_NAME = your_bot_name

command = your_command_to_restart
apiKey = your_api_key
apiSecret = your_api_secret
header = {"X-MBX-APIKEY": apiKey}
db_path = your_database_path


```
* Create data folder.
* Run database.py once to create the database and tables.


### Newest Release:
V0.3:
* Almost completely rewrites the code of the bot to optimise processes and cutting cpu usage by 33%.
* Uses a new class for user's portfolio, crypto assets and rewrites the strategy class.
* Cut the bot class nearly in half for clearer reading of the code.

v0.2.5:
* Rebalances long term positions with new deposits or profit made from other trades

v0.2:
* Overhauls the financial management system.
* Moves the bot to his own class.
* Streamlines installation

v0.1:
* Initial release

### Under Development:

* Any bug fixes that may arise during testing
* Adding a notification system when trade orders have been placed.
* A weekly summary displaying how the bot has performed.
* A selling strategy if desired
