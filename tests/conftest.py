import pytest

from src.entity.deep import Deep
from src.entity.order import MarketOrder
from src.entity.order_book import OrderBook
from src.entity.symbol import Symbol
from src.enums import SymbolType, Currency, OrderAction


@pytest.fixture(scope='session')
def symbol1():
    return Symbol('symbol1', 'exchange1', SymbolType.STOCK, Currency.USD)


@pytest.fixture(scope='function')
def market_buy_order():
    return MarketOrder(Symbol('symbol1', 'exchange1', SymbolType.STOCK, Currency.USD), 300, OrderAction.BUY)


@pytest.fixture(scope='function')
def market_sell_order():
    return MarketOrder(Symbol('symbol1', 'exchange1', SymbolType.STOCK, Currency.USD), 300, OrderAction.SELL)


@pytest.fixture(scope='function')
def orderbook_2x2():
    return OrderBook(Deep(2, 2))
