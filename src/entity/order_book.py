from threading import Thread
from uuid import uuid4
from src.entity.deep import Deep
from src.entity.market_data import MarketData
from src.entity.order import Order, MarketOrder
from src.enums import OrderAction, OrderStatus, OrderType
from src.exception import OrderAlreadyCreatedError, ChangeOrderBookDeepError, SymbolIsNotEnabledError
from src.utils.quotes_generator import quote_generator


class OrderBook:
    """
    The OrderBook object realize the methods and logic with orders

    :param deep: one of the property of order book that characterizes the number of visible orders.
    """

    def __init__(self, deep: Deep):
        self.orders = list()
        self.deep = None
        self.set_deep(deep)
        self.quotes = quote_generator

    def set_deep(self, deep: Deep) -> None:
        """
        This method provides an ability to set order book's deep on the fly.
        If some of deep's parameters is <0 (bid_count or ask_count) then method raise the custom
        ChangeOrderBookDeepError exception.

        :param deep: one of the property of order book that characterizes the number of visible orders.
        :return None
        """

        def is_deep_invalid(var: Deep):
            return not isinstance(var, Deep) \
                   or False in [str(value).isdigit() for value in deep.__dict__.values()] \
                   or deep.bid_count < 0 \
                   or deep.ask_count < 0

        # Exit rule
        if is_deep_invalid(deep):
            raise ChangeOrderBookDeepError(deep)
        self.deep = deep

    def _place_market_order(self, order: MarketOrder):
        order.price = self.quotes.get_current_quote(order.symbol)
        order.status = OrderStatus.PENDING
        self.orders.append(order)
        print(f"Order {order.__dict__} is placed.")

    def _place_limit_order(self, order):
        order.status = OrderStatus.PENDING
        self.orders.append(order)
        print(f"Order {order.__dict__} is placed.")

    def _place_stop_order(self, order):
        if order.action == OrderAction.SELL:
            while True:
                current_market_price = self.quotes.get_current_quote(order.symbol)
                if order.price >= current_market_price:
                    order.price = current_market_price
                    order.type = OrderType.MARKET
                    order.status = OrderStatus.PENDING
                    self.orders.append(order)
                    print(f"Order {order.__dict__} is placed.")
                    return

        elif order.action == OrderAction.BUY:
            while True:
                current_market_price = self.quotes.get_current_quote(order.symbol)
                if order.price <= current_market_price:
                    order.price = current_market_price
                    order.type = OrderType.MARKET
                    order.status = OrderStatus.PENDING
                    self.orders.append(order)
                    print(f"Order {order.__dict__} is placed.")
                    return

    def _place_stop_limit_order(self, order):
        if order.action == OrderAction.SELL:
            while True:
                current_market_price = self.quotes.get_current_quote(order.symbol)
                if order.stop_price >= current_market_price:
                    order.type = OrderType.LIMIT
                    order.status = OrderStatus.PENDING
                    self.orders.append(order)
                    print(f"Order {order.__dict__} is placed.")
                    return

        if order.action == OrderAction.BUY:
            while True:
                current_market_price = self.quotes.get_current_quote(order.symbol)
                if order.stop_price <= current_market_price:
                    order.type = OrderType.LIMIT
                    order.status = OrderStatus.PENDING
                    self.orders.append(order)
                    print(f"Order {order.__dict__} is placed.")
                    return

    def __place_order(self, order):
        if order.type == OrderType.MARKET:
            self._place_market_order(order)
        elif order.type == OrderType.LIMIT:
            self._place_limit_order(order)
        elif order.type == OrderType.STOP:
            self._place_stop_order(order)
        elif order.type == OrderType.STOP_LIMIT:
            self._place_stop_limit_order(order)

    def place_order(self, order: Order) -> None:
        """
        This method provide an ability to place an order in order book.
        After each addition of order the list will be resorted by price (first orders
        contains the highest price)

        Assertions:
        1. If order book already has order with order.id then method raise
        OrderAlreadyCreatedError exception. It's protect from duplicates.
        2. If order is not enabled then method raise SymbolIsNotEnabledError exception.
        It so because you cannot place order for symbol that is not ready for trading.
        3. Only Market Order and Limit Order will be placed imediatelly. Stop Order, StopLimit orders
        will be placed when price will be triggered.

        :param order: order for buy or sell some instrument on exchange
        :return: None
        """

        if order.id in [order.id for order in self.orders]:
            raise OrderAlreadyCreatedError(order)

        if not order.symbol.is_enabled:
            raise SymbolIsNotEnabledError(order.symbol)

        t = Thread(target=self.__place_order, args=(order,))
        t.start()

        self.__sort_orders_by_price()

    def __sort_orders_by_price(self):
        """
        Private method that provide an ability to sort the orders by price

        :return: None
        """
        self.orders = sorted(self.orders, key=lambda o: o.price, reverse=True)

    def get_orders_by_action(self, action: OrderAction, count: int = None) -> list:
        """
        This method provide an ability to get order from order book by order action (sell or buy).
        By other words - you can get asks or bids here.


        :param action: buy or sell. Use OrderAction.BUY for bid or OrderAction.SELL for ask.
        :param count: how much orders you would like to see.
        For example count=1 return the order with most low price (if ask) or high price (if bid)
        :return: list of orders without any filters. You will see orders with any status and symbol
        """
        if not isinstance(count, int) and count is not None:
            return list()
        return [order for order in self.orders if order.action == action][:count]

    def reject_order(self, order: Order) -> None:
        """
        This method provide an ability to find order by id and reject it.
        For example: It can be helpful if account don't have enough many for place an order.

        :param order: order. It can be market,limit,stop,stop limit order.
        :return: None
        """
        order = self.get_order_by_id(order.id)
        order.status = OrderStatus.REJECT

    def fill_order(self, order: Order) -> None:
        """
        This method provide an ability to fill order in order book.
        This action means that order is completed.

        :param order: order id. It can be market,limit,stop,stop limit order.
        :return: None
        """
        order = self.get_order_by_id(order.id)
        order.status = OrderStatus.FILL

    def cancel_order(self, order: Order) -> None:
        self.get_order_by_id(order.id).status = OrderStatus.CANCEL

    def get_order_by_id(self, order_id: uuid4) -> Order:
        """
        This method provide an ability to find and return order by using order id.

        :param order_id: order id. Recommend to generate id by using function uuid.uuid4().
        :return: list of orders without any filters. You will see orders with any status and symbol
        """
        return next(filter(lambda order: order.id == order_id, self.orders), None)

    def get_market_data(self) -> dict:
        """
        This method provide an ability to get a market data snapshot.
        For example it can be helpful when you need to print order book or sent it to someone.

        :return: data by following json:
        {
            "asks": [
                {
                    "price": value : float,
                    "quantity": value : float
                },
                ...
            ],
            "bids": [
                {
                    "price": value : float,
                    "quantity": value: float
                },
                ...
            ]
        """
        return MarketData(asks=self.get_orders_by_action(OrderAction.SELL, self.deep.ask_count),
                          bids=self.get_orders_by_action(OrderAction.BUY, self.deep.bid_count)).format

    def get_best_price(self, action: OrderAction, count: int = None) -> list:
        return sorted(self.get_orders_by_action(action), key=lambda x: x.price)[:count]