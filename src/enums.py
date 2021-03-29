from enum import Enum


class Currency(Enum):
    EUR = "eur"
    USD = "usd"
    RUB = "rub"
    CRYPTO = "crypto"


class SymbolType(Enum):
    STOCK = "stock"
    FUTURE = "future"
    FOREX = "forex"
    OPTION = "option"


class OrderType(Enum):
    LIMIT = "limit"
    MARKET = "market"
    STOP = 'stop'
    STOP_LIMIT = 'stop limit'


class OrderAction(Enum):
    BUY = 'buy'
    SELL = 'sell'


class OrderStatus(Enum):
    FILL = "fill"
    REJECT = 'reject'
    PENDING = 'pending'
    CANCEL = 'cancel'
    CREATED = 'created'