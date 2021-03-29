# order_book
Test repository for demonstrate my skills in python and pytest

# Structure
#### src
Order book realization. All code that emulates the orderbook's workflow (partially) here

#### src.conf
Yml config file for quote_generator and config parser. Not so interested

#### src.entity
All entities that order book use such as order book's deep, market data, order, order book, symbol

#### src.utils
Some other utils that should help automation qa to create automated tests for order book such as jsonschema_validators.
Also, here is quotes_generator, the main goal is to generate quote for symbols (list of symbol is defined in configs).

#### tests
#### tests.tests.py
Here is all tests for order book, deep, order.
I will continue to write new tests here (need to write for symbol, market data)

#### tests.conftests.py
Here is fixtures.

#### requirements.txt
All required libraries.


# How to run?
1. Install requirements `pip3 install -r requirements.txt`
2. Run tests `pytest tests/tests.py`

