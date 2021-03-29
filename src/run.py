import time

from src.entity.order_book import OrderBook
from src.entity.deep import Deep
from src.entity.order import MarketOrder, LimitOrder, StopLimitOrder, StopOrder
from src.entity.symbol import Symbol
from src.enums import OrderAction, SymbolType, Currency

deep = Deep(4, 4)
order_book = OrderBook(deep)

symbol1 = Symbol('symbol1', 'exchange1', SymbolType.STOCK, Currency.EUR, is_enabled=True)
symbol2 = Symbol('symbol2', 'exchange1', SymbolType.OPTION, Currency.USD, is_enabled=True)

order1 = MarketOrder(symbol1, 2.5, OrderAction.BUY)
order2 = LimitOrder(symbol2, 1500, 12, OrderAction.SELL)
order3 = StopOrder(symbol1, 70, 20, OrderAction.BUY)
order4 = StopLimitOrder(symbol2, 70, 80, 2.5, OrderAction.SELL)
print(f"Order1 is {order1.__dict__}\nOrder2 is {order2.__dict__}\nOrder3 is {order3.__dict__}\nOrder4 is {order4.__dict__}")

order_book.place_order(order1)
order_book.place_order(order2)
order_book.place_order(order3)
order_book.place_order(order4)

while len(order_book.orders) < 4:
    print(order_book.get_market_data())
    time.sleep(5)
print(order_book.get_market_data())
