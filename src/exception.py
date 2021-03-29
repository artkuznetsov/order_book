from abc import ABC

from src.entity.deep import Deep
from src.entity.symbol import Symbol


class OrderAlreadyCreatedError(Exception):
    """Exception for cases when somebody tries to add order to order book that already created (match by order.id)"""
    def __init__(self, order):
        self.msg = f"The order {order.id} is already created. "


class ChangeOrderBookDeepError(Exception):
    """Exception for cases when somebody tries to change order book's deep"""
    def __init__(self, deep: Deep):
        self.msg = f"The deep {deep} is not valid. Probably, asks_count or bids_count are les then 0. "
        super().__init__(self.msg)


class OrderPriceIsNotValidError(Exception):
    """Exception for cases when somebody tries to set price < 0 ofr order"""
    def __init__(self, price: float):
        self.msg = f"The order's price {price} is less or equals 0. "
        super().__init__(self.msg)


class OrderChangeWhenPlacedError(Exception):
    """Exception for cases when somebody tries to change order's parameter if order is already placed."""
    def __init__(self, order):
        self.msg = f"The order {order} cannot be changed after placing. "
        super().__init__(self.msg)


class OrderQuantityIsNotValidError(Exception):
    """Exception for cases when somebody tries to set price < 0 ofr order"""
    def __init__(self, quantity: float):
        self.msg = f"The order's quantity {quantity} is not valid. "


class SymbolIsNotEnabledError(Exception):
    """Exception for cases when somebody tries to trade by using not enabled symbol"""
    def __init__(self, symbol: Symbol):
        self.msg = f"The symbol {symbol} is not enabled. "


class SymbolIsNotValidError(Exception):
    """Exception for cases when somebody tries to trade by using not enabled symbol"""
    def __init__(self, symbol: Symbol):
        self.msg = f"The symbol {symbol} is not valid. "
