from abc import ABC
from uuid import uuid4, UUID
from src.entity.symbol import Symbol
from src.enums import OrderType, OrderAction, OrderStatus
from src.exception import OrderPriceIsNotValidError, OrderQuantityIsNotValidError, SymbolIsNotValidError,\
    OrderChangeWhenPlacedError


class Order(ABC):
    """
    The Order object realize the methods and logic for order.
    """

    def __init__(self, symbol: Symbol, price: float, quantity: float, order_type: OrderType, order_action: OrderAction):
        self.status = None
        self.symbol = symbol
        self.quantity = quantity
        self.type = order_type
        self.price = price
        self.action = order_action
        self.id = uuid4()

    def __repr__(self) -> str:
        return str(self.__dict__)

    @property
    def id(self) -> uuid4:
        """
        This method is just getter for order id.

        :return: order id
        """
        return self._id

    @property
    def symbol(self) -> Symbol:
        return self._symbol

    @symbol.setter
    def symbol(self, value: Symbol) -> None:
        if self.is_placed():
            raise OrderChangeWhenPlacedError(self)
        if not isinstance(value, Symbol):
            raise SymbolIsNotValidError(value)

        self._symbol = value

    @property
    def price(self) -> float:
        """
        This method is just getter for order price

        :return: order price
        """
        return self._price

    @price.setter
    def price(self, value: float) -> None:
        """
        This method is setter for price with one internal assertion:
        order price cannot be < 0. If so, method raise the
        OrderPriceIsLessThanZeroError exception.

        :param value: order price
        :return: None
        """
        if type(value) in (int, float) and value > 0 and not self.is_placed():
            self._price = value
        else:
            raise OrderPriceIsNotValidError(value)

    @property
    def quantity(self) -> float:
        """
        This method is just getter for order's quantity

        :return: order quantity (how much symbols you would like to sell/buy)
        """
        return self._quantity

    @quantity.setter
    def quantity(self, value: float) -> None:
        """
        This method is just setter for order quantity with one internal assertion:
        order's quantity cannot be 0 or less. If so, method raise the
        OrderQuantityIsLessThanZeroError exception.

        :param value: how much symbols you would like to sell/buy
        :return: None
        """
        if type(value) in (int, float) and value > 0:
            self._quantity = value
            return
        raise OrderQuantityIsNotValidError(value)

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, value: OrderType):
        if self.is_placed():
            raise OrderChangeWhenPlacedError(self)
        if isinstance(value, OrderType):
            self._type = value
        else:
            raise ValueError(f"Order's type {value} is not valid. ")

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value: OrderStatus):
        self._status = value

    @property
    def action(self):
        return self._action

    @action.setter
    def action(self, value: OrderAction):
        self._action = value

    @id.setter
    def id(self, value: UUID):
        if self.is_placed():
            raise OrderChangeWhenPlacedError(self)
        elif isinstance(value, UUID):
            self._id = value
        else:
            raise ValueError(f"The id {value} is not unique identification (UUID). ")

    def is_placed(self):
        return self.status is not None


class MarketOrder(Order):
    def __init__(self, symbol: Symbol, quantity: float, order_action: OrderAction):
        super().__init__(symbol, 0.0001, quantity, OrderType.MARKET, order_action)


class LimitOrder(Order):
    def __init__(self, symbol: Symbol, price: float, quantity: float, order_action: OrderAction):
        super().__init__(symbol, price, quantity, OrderType.LIMIT, order_action)


class StopLimitOrder(Order):
    def __init__(self, symbol: Symbol, limit_price: float, stop_price: float, quantity: float,
                 order_action: OrderAction):
        super().__init__(symbol, limit_price, quantity, OrderType.STOP_LIMIT, order_action)
        self.stop_price = stop_price


class StopOrder(Order):
    def __init__(self, symbol: Symbol, stop_price: float, quantity: float, order_action: OrderAction):
        super().__init__(symbol, stop_price, quantity, OrderType.STOP, order_action)
