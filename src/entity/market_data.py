from dataclasses import dataclass, asdict

from src.enums import OrderStatus, OrderType


@dataclass
class MarketData:
    """
    This class contains the formated order book's data (bids and asks)
    """
    asks: list
    bids: list

    @staticmethod
    def __check_order_is_ready_for_market_data(order):
        return (order.status not in (OrderStatus.REJECT, OrderStatus.FILL)) \
                    and (order.type in (OrderType.MARKET, OrderType.LIMIT))

    @property
    def format(self) -> dict:
        """
        This method provide an ability to format order's book data by following type:
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


            !!! One important thing: you will not see orders with "reject" or "fill" statuses. !!!
        :return: dict
        """
        for i in range(len(self.asks)):
            if self.__check_order_is_ready_for_market_data(self.asks[i]):
                self.asks[i] = {'price': self.asks[i].price, 'quantity': self.asks[i].quantity}

        for i in range(len(self.bids)):
            if self.__check_order_is_ready_for_market_data(self.bids[i]):
                self.bids[i] = {'price': self.bids[i].price, 'quantity': self.bids[i].quantity}
        return asdict(self)