import uuid
from typing import Union
from uuid import UUID
from retrying import retry

import pytest

from src.entity.deep import Deep
from src.entity.order import MarketOrder, LimitOrder, Order, StopOrder, StopLimitOrder
from src.entity.order_book import OrderBook
from src.entity.symbol import Symbol
from src.enums import SymbolType, Currency, OrderAction, OrderStatus, OrderType
from src.exception import ChangeOrderBookDeepError, OrderPriceIsNotValidError, SymbolIsNotValidError, \
    OrderQuantityIsNotValidError, OrderChangeWhenPlacedError

from src.utils.jsonschema_validators import is_market_data_schema_valid
from src.utils.quotes_generator import quote_generator


def try_create_order(order: MarketOrder or LimitOrder or StopLimitOrder or StopOrder, *args) \
        -> Union[Order, OrderPriceIsNotValidError, Exception]:
    try:
        return order(*args)
    except Exception as e:
        return e


@retry(stop_max_delay=20000)
def check_order_status(order, status):
    assert order.status == status


class TestOrder:
    def test_id__get(self, market_buy_order):
        """
        @description:
        Here we would like to make sure that client can get id of order

        @pre-conditions:
        1. create any order (market_buy_order)

        @steps:
        1. get order's id

        @assertions:
        1. order has id
        2. type of order's id is uniquie identificator (UUID)
        """
        assert market_buy_order.id
        assert isinstance(market_buy_order.id, UUID)

    @pytest.mark.parametrize("test_id,is_it_positive_case", [
        (100, False), (uuid.uuid4(), True), (0, False), ("ABC", False),
        (None, False), (uuid.uuid1(), True)
    ])
    def test_id__set(self, test_id, is_it_positive_case, market_buy_order):
        """
        @description:
        Here we would like to make sure that client can set id of order.

        @pre-conditions:
        1. Create any order (market_buy_order)

        @parameters:
        test_id: value that we would like to put to order.id
        is_it_positive_case: flag. "True" value means that test_id is valid and test should be passed.
                             "False" value means that test_id is invalid and test shouldn't be passed

        @steps:
        1. Try to set test_id to order

        @assertions:
        2. If test_id is valid that order's id should be equal to test_id
        1. If test_id is invalid that client should recive the specify error message
        """
        try:
            market_buy_order.id = test_id
        except ValueError as e:
            assert not is_it_positive_case
            assert e.args[0] == f"The id {test_id} is not unique identification (UUID). "
            return
        assert is_it_positive_case
        assert market_buy_order.id == test_id

    @pytest.mark.parametrize("test_id", [100, uuid.uuid4(), 0, "ABC", None, uuid.uuid1()])
    def test_id__set_after_placing(self, test_id, market_buy_order, orderbook_2x2):
        """
        @description:
        Here we would like to make sure that client cannot set order's id if order already placed.

        @pre-conditions:
        1. Create any order (market_buy_order)

        @parameters:
        test_id: value that we would like to put to order.id
        orderbook_2x2: order book for place our order

        @steps:
        1. Place order
        2. Try to set test_id to order

        @assertions:
        1. User cannot change the order's id. Client received an error message like
           "The order {market_buy_order} cannot be changed after placing. ". Test is passed.
        2. If order's id is changed - it's a bug and test should be failed.
        """
        orderbook_2x2.place_order(market_buy_order)
        try:
            market_buy_order.id = test_id
        except OrderChangeWhenPlacedError as e:
            assert e.msg == f"The order {market_buy_order} cannot be changed after placing. "
            return
        pytest.fail("[ERROR] Order's id is changed after place but shouldn't be.")

    def test_symbol__get(self, symbol1, market_buy_order):
        """
        @description:
        Here we would like to make sure that client can get order's symbol

        @pre-conditions:
        1. Create symbol (symbol1)
        2. Create order (market_buy_order) with symbol1

        @steps:
        1. Get symbol from order

        @assertions:
        1. Order's symbol is equals to symbol1
        """
        assert market_buy_order.symbol == symbol1

    @pytest.mark.parametrize("test_symbol,is_it_positive_case", [
        (Symbol('symbol1', 'exchange1', SymbolType.STOCK, Currency.USD), True),
        ('symbol1', False), (100, False), ("ABC", False)
    ])
    def test_symbol__set(self, test_symbol, is_it_positive_case, market_buy_order):
        """
        @description:
        Here we would like to make sure that client can set symbol to order

        @pre-conditions:
        1.Create order (market_buy_order)

        @parameters:
        test_symbol: valid/invalid data that we would like to put to order as symbol
        is_it_positive_case: flag. "True" value means that test_symbol is valid and test should be passed.
                             "False" value means that test_symbol is invalid and test shouldn't be passed

        @steps:
        1. Try to set test_symbol to order

        @assertions:
        1. If test_symbol is valid that order's symbol should be changed. Test is passed
        2. If test_symbol is invalid that order's symbol shouldn't be changed. Client should recive an error message
           like "The symbol {test_symbol} is not valid. ". Test is failed.
        """
        # TODO: Need to add the another test for case when id cannot be set if order.status is CREATED
        try:
            market_buy_order.symbol = test_symbol
        except SymbolIsNotValidError as e:
            assert not is_it_positive_case
            assert e.msg == f"The symbol {test_symbol} is not valid. "
            return
        assert is_it_positive_case
        assert market_buy_order.symbol == test_symbol

    @pytest.mark.parametrize("test_price,is_it_positive_case", [
        (100, True), (0.001, True), (pow(2, 2048), True), (1, True), (0, False),
        (-5, False), (-0.001, False), ("ABC", False), (True, False), (None, False)
    ])
    def test_price__set__before_placing(self, test_price, is_it_positive_case, market_buy_order):
        """
        @description:
        Here we would like to make sure that client can set order's price before placing

        @pre-conditions:
        1. Create order (market_buy_order)

        @parameters:
        test_price: valid/invalid data that we would like to put to order as price
        is_it_positive_case: flag. "True" value means that test_price is valid and test should be passed.
                             "False" value means that test_price is invalid and test shouldn't be passed

        @steps:
        1. Try to change order's price to test_price

        @assertions:
        1. If test_price is valid that order's price should be changed. Test is passed.
        2. If test_price is invalid that order's price shouldn't be changed. Client should receive an error message
           like "The order's price {test_price} is less or equals 0. "

        """
        try:
            market_buy_order.price = test_price
        except OrderPriceIsNotValidError as e:
            assert not is_it_positive_case
            assert e.msg == f"The order's price {test_price} is less or equals 0. "
            return
        assert market_buy_order.price == test_price

    def test_quantity__get(self, symbol1):
        """
        @description:
        Here we would like to make sure that client can get order's quantity

        @pre-conditions:
        symbol1: default stock symbol with "symbol1" name

        @steps:
        1. Create order with quantity = 300 (for example)

        @assertions:
        1. Order's quantity is changed. Test is passed
        """
        quantity = 300
        order = MarketOrder(symbol1, quantity, OrderAction.BUY)
        assert order.quantity == quantity

    @pytest.mark.parametrize("test_quantity,is_it_positive_case", [
        (1, True), (pow(2, 2048), True), (0.0001, True), (1 + 13, True),
        (0, False), (-1, False), (-0.0001, False), ("ABC", False),
        (None, False), (True, False)
    ])
    def test_quantity__set(self, test_quantity, is_it_positive_case, market_buy_order):
        """
        @description:
        Here we would like to make sure that client can get quantity from order before place.

        @pre-conditions:
        1. Create order (market_buy_order)

        @parameters:
        test_quantity: valid/invalid data that we would like to put to order as quantity
        is_it_positive_case: flag. "True" value means that test_quantity is valid and test should be passed.
                             "False" value means that test_quantity is invalid and test shouldn't be passed

        @steps:
        1. Try to change order's quantity

        @assertions:
        1. If test_quantity is valid that order's quantity should be changed. Test is passed
        2. If test_quantity is invalid that order's quantity shouldn'e be changed. Client received an error message
           like "The order's quantity {test_quantity} is not valid. ". Test is failed.
        """
        try:
            market_buy_order.quantity = test_quantity
        except OrderQuantityIsNotValidError as e:
            assert not is_it_positive_case
            assert e.msg == f"The order's quantity {test_quantity} is not valid. "
            return

        assert market_buy_order.quantity == test_quantity

    @pytest.mark.parametrize("test_price", [
        1, pow(2, 2048), 0.0001, 1 + 13, 0, -1, -0.0001, "ABC", None, True
    ])
    def test_price__set_after_placing(self, test_price, market_buy_order, orderbook_2x2):
        """
        @description:
        Here we would like to make sure that client cannot set order's price if order is already placed.

        @pre-conditions:
        1. Create order (market_buy_order)
        2. Create order book (orderbook_2x2)

        @parameters:
        test_price: valid/invalid data that we would like to put to order as price

        @steps:
        1. Place the order to order book
        2. Try to change order's price

        @assertions:
        1. Client received an error message like "The order's price {test_price} is less or equals 0. ". Test is passed.
        2. If order's price is changed - it's a bug. Test is failed
        """
        orderbook_2x2.place_order(market_buy_order)

        try:
            market_buy_order.price = test_price
        except OrderPriceIsNotValidError as e:
            assert e.msg == f"The order's price {test_price} is less or equals 0. "
            return
        pytest.fail("[ERROR] Order's price is set but shouldn't!")

    def test_type__get__market_order(self, market_buy_order):
        """
        @description:
        Here we would like to make sure that client get order's type from market order

        @pre-conditions:
        1. Create order (market_buy_order)

        @steps:
        1. Get order's type

        @assertions:
        Order's type should be MARKET. Test is passed

        """
        assert market_buy_order.type == OrderType.MARKET

    def test_type__get__limit_order(self, symbol1):
        """
        @description:
        Here we would like to make sure that client get order's type from limit order

        @pre-conditions:
        1. Create symbol (symbol1)

        @steps:
        1. Create order with symbol1
        2. Get order's type

        @assertions:
        Order's type should be LIMIT. Test is passed
        """
        order = LimitOrder(symbol1, 100, 25, OrderAction.BUY)
        assert order.type == OrderType.LIMIT

    def test_type__get__stop_order(self, symbol1):
        """
        @description:
        Here we would like to make sure that client get order's type from stop order

        @pre-conditions:
        1. Create symbol (symbol1)

        @steps:
        1. Create order with symbol1
        2. Get order's type

        @assertions:
        Order's type should be STOP. Test is passed
        """
        order = StopOrder(symbol1, 100, 25, OrderAction.BUY)
        assert order.type == OrderType.STOP

    def test_type__get__stop_limit_order(self, symbol1):
        """
        @description:
        Here we would like to make sure that client get order's type from stop limit order

        @pre-conditions:
        1. Create symbol (symbol1)

        @steps:
        1. Create order with symbol1
        2. Get order's type

        @assertions:
        Order's type should be STOP_LIMIT. Test is passed
        """
        order = StopLimitOrder(symbol1, 50, 100, 0.24, OrderAction.SELL)
        assert order.type == OrderType.STOP_LIMIT

    def test_status__get___market_before_placing(self, market_buy_order):
        """
        @description:
        Here we would like to make sure that order's don't have status before placing in order book

        @pre-conditions:
        1. Create order (market_buy_order)

        @assertions:
        1. Order's status is None
        """
        check_order_status(market_buy_order, None)

    def test_status__get__market_after_placing(self, market_buy_order, orderbook_2x2):
        """
        @description:
        Here we would like to make sure that market order's status is changed after placing

        @pre-conditions:
        1. Create order (market_buy_order)
        2. Create order book (orderbook_2x2)

        @steps:
        1. Place the order

        @assertions:
        Order's status is Pending. Test is passed
        """
        orderbook_2x2.place_order(market_buy_order)

        check_order_status(market_buy_order, OrderStatus.PENDING)

    def test_status__get__sell_stop_after_placing(self, symbol1, orderbook_2x2):
        """
        @description:
        Here we would like to make sure that sell stop order's status is changed after placing

        @pre-conditions:
        1. Create symbol (symbol1)
        2. Create order book (orderbook_2x2)

        @steps:
        1. Create Sell Stop order
        2. Place the order
        3. Wait until current price for symbol1 > order's price

        @assertions:
        Order's status is Pending. Test is passed
        """
        order = StopOrder(symbol1, 90, 25, OrderAction.SELL)
        orderbook_2x2.place_order(order)

        while quote_generator.get_current_quote(symbol1) > order.price:
            ...
        check_order_status(order, OrderStatus.PENDING)

    def test_status__get__buy_stop_after_placing(self, symbol1, orderbook_2x2):
        """
        @description:
        Here we would like to make sure that buy stop order's status is changed after placing

        @pre-conditions:
        1. Create symbol (symbol1)
        2. Create order book (orderbook_2x2)

        @steps:
        1. Create Buy Stop order
        2. Place the order
        3. Wait until current price for symbol1 < order's price

        @assertions:
        Order's status is Pending. Test is passed
        """
        order = StopOrder(symbol1, 130, 25, OrderAction.BUY)
        orderbook_2x2.place_order(order)

        while quote_generator.get_current_quote(symbol1) < order.price:
            ...

        check_order_status(order, OrderStatus.PENDING)

    def test_status__get__sell_stop_limit_after_placing(self, symbol1, orderbook_2x2):
        """
        @description:
        Here we would like to make sure that buy sell stop limit order's status is changed after placing

        @pre-conditions:
        1. Create symbol (symbol1)
        2. Create order book (orderbook_2x2)

        @steps:
        1. Create Sell Stop Limit order
        2. Place the order
        3. Wait until current price for symbol1 >= order's price

        @assertions:
        Order's status is Pending. Test is passed
        """
        order = StopLimitOrder(symbol1, 70, 75, 25, OrderAction.SELL)
        orderbook_2x2.place_order(order)
        while quote_generator.get_current_quote(symbol1) >= order.stop_price:
            ...

        check_order_status(order, OrderStatus.PENDING)

    def test_status__get__buy_stop_limit_after_placing(self, symbol1, orderbook_2x2):
        """
        @description:
        Here we would like to make sure that buy buy stop limit order's status is changed after placing

        @pre-conditions:
        1. Create symbol (symbol1)
        2. Create order book (orderbook_2x2)

        @steps:
        1. Create Sell Stop Limit order
        2. Place the order
        3. Wait until current price for symbol1 >= order's price

        @assertions:
        Order's status is Pending. Test is passed
        """
        order = StopLimitOrder(symbol1, 135, 130, 25, OrderAction.BUY)
        orderbook_2x2.place_order(order)
        while quote_generator.get_current_quote(symbol1) <= order.stop_price:
            ...

        check_order_status(order, OrderStatus.PENDING)


class TestOrderBook:

    @pytest.mark.parametrize("test_order_action,is_it_positive_case", [
        (OrderAction.BUY, True), (OrderAction.SELL, True), (OrderType.MARKET, False)
    ])
    def test_place_order__market_order(self, test_order_action, is_it_positive_case, symbol1, orderbook_2x2):
        """
        @description:
        Here we would like to make sure that client can place market order

        @pre-conditions:
        1. Create symbol (symbol1)
        2. Create order book (orderbook_2x2)

        @parameters:
        test_order_action: valid/invalid data that we would like to put to order's action
        is_it_positive_case: flag. "True" value means that test_order_action is valid and test should be passed.
                             "False" value means that test_order_action is invalid and test shouldn't be passed

        @steps:
        1. Try to create market order with test_order_action
        2. Place the order
        3. Get current quote for symbol1

        @assertions:
        1. Order's price is changed to current quote for symbol1.
        2. Order is placed.
        3. Order's action is test_order_action
        """
        result = try_create_order(MarketOrder, symbol1, 13, test_order_action)

        orderbook_2x2.place_order(result)
        current_quote = quote_generator.get_current_quote(symbol1)

        assert result.price == current_quote
        assert result.is_placed()
        assert result.action == test_order_action

    @pytest.mark.parametrize("test_order_price,is_it_positive_case", [
        (120, True), (0, False), (0.001, True), ('ABC', False), (-0.25, False),
        (None, False), (True, False)
    ])
    def test_place_order__limit_order(self, test_order_price, is_it_positive_case, symbol1, orderbook_2x2):
        """
        @description:
        Here we would like to make sure that client can place limit order

        @pre-conditions:
        1. Create symbol (symbol1)
        2. Create order book (orderbook_2x2)

        @parameters:
        test_order_price: valid/invalid data that we would like to put to order's price
        is_it_positive_case: flag. "True" value means that test_order_pricen is valid and test should be passed.
                             "False" value means that test_order_price is invalid and test shouldn't be passed

        @steps:
        1. Try to create limit order with test_order_price
        2. Place the order

        @assertions:
        1. Order's price is changed to current quote for symbol1.
        2. Order is placed.
        3. If test_order_price is invalid that client should receive an error message like
           "The order's price {test_order_price} is less or equals 0. "
        """
        result = try_create_order(LimitOrder, symbol1, test_order_price, 30, OrderAction.BUY)

        # result can be equal to Order or Exception
        if not is_it_positive_case:
            assert isinstance(result, OrderPriceIsNotValidError)
            assert result.msg == f"The order's price {test_order_price} is less or equals 0. "
            return

        orderbook_2x2.place_order(result)

        assert result.price == orderbook_2x2.get_order_by_id(result.id).price
        assert result.is_placed()

    @pytest.mark.parametrize("test_order_price,is_it_positive_case", [
        (50, True), (0, False), (0.001, True), ('ABC', False), (-0.25, False),
        (None, False), (True, False)
    ])
    def test_place_order__stop_order(self, test_order_price, is_it_positive_case, symbol1, orderbook_2x2):
        """
        @description:
        Here we would like to make sure that client can place stop order

        @pre-conditions:
        1. Create symbol (symbol1)
        2. Create order book (orderbook_2x2)

        @parameters:
        test_order_price: valid/invalid data that we would like to put to order's price
        is_it_positive_case: flag. "True" value means that test_order_pricen is valid and test should be passed.
                             "False" value means that test_order_price is invalid and test shouldn't be passed

        @steps:
        1. Try to create limit order with test_order_price
        2. Place the order

        @assertions:
        1. Order's price is changed to current quote for symbol1.
        2. Order is placed.
        3. If test_order_price is invalid that client should receive an error message like
           "The order's price {test_order_price} is less or equals 0. "
        """
        result = try_create_order(StopOrder, symbol1, test_order_price, 0.25, OrderAction.BUY)

        # result can be equal to Order or Exception
        if not is_it_positive_case:
            assert isinstance(result, OrderPriceIsNotValidError)
            assert result.msg == f"The order's price {test_order_price} is less or equals 0. "
            return

        orderbook_2x2.place_order(result)

        assert test_order_price <= orderbook_2x2.get_order_by_id(result.id).price
        assert result.is_placed()

    @pytest.mark.parametrize("test_order_action,is_it_positive_case", [
        (OrderAction.BUY, True), (OrderAction.SELL, False), ('buy', False),
        ('sell', False), ('BUY', False), ('SELL', False), (OrderAction, False)
    ])
    def test_get_order_by_action__check_action(self, test_order_action, is_it_positive_case, market_buy_order, orderbook_2x2):
        """
        @description:
        Here we would like to make sure that client can get orders by action type

        @pre-conditions:
        1. Create order (market_buy_order)
        2. Create order book (orderbook_2x2)

        @parameters:
        test_order_action: valid/invalid data that we would like to put to order as action
        is_it_positive_case: flag. "True" value means that test_order_action is valid and test should be passed.
                             "False" value means that test_order_action is invalid and test shouldn't be passed

        @steps:
        1. Place order

        @assertions:
        1. If test_order_action is valid that client received list of orders by type
        2. If test_order_action is invalid that client received empty list
        """
        orderbook_2x2.place_order(market_buy_order)
        if is_it_positive_case:
            assert orderbook_2x2.get_orders_by_action(test_order_action) == [market_buy_order]
        else:
            assert orderbook_2x2.get_orders_by_action(test_order_action) == []

    @pytest.mark.parametrize("test_order_action,count,is_it_positive_case", [
        (OrderAction.BUY, 1, True), (OrderAction.SELL, 2, True), ('buy', 0, False),
        ('sell', 0, False), ('BUY', 0, False), ('SELL', 0, False), (OrderAction, 0, False)
    ])
    def test_get_order_by_action__check_count(self, test_order_action, count, is_it_positive_case, symbol1, orderbook_2x2):
        """
        @description:
        Here we would like to make sure that count of orders received by action filtering is correct

        @pre-conditions:
        1. Create symbol (symbol1)
        2. Create order book (orderbook_2x2)

        @parameters:
        test_order_action: valid/invalid data that we would like to put to order as action
        count: expected count of orders by some order action
        is_it_positive_case: flag. "True" value means that test_order_action and count are valid and test should be passed.
                             "False" value means that test_order_action and count are invalid and test shouldn't be passed

        @steps:
        1. Create 1 BUY order
        2. Create 2 SELL order
        3. Place all created orders

        @assertions:
        1. If test_order_action is valid that count of orders by this action is correct
        2. If test_order_action is invalid that client received empty list
        """
        order1 = MarketOrder(symbol1, 0.25, OrderAction.BUY)
        order2 = MarketOrder(symbol1, 1, OrderAction.SELL)
        order3 = MarketOrder(symbol1, 1, OrderAction.SELL)
        orderbook_2x2.place_order(order1)
        orderbook_2x2.place_order(order2)
        orderbook_2x2.place_order(order3)
        if is_it_positive_case:
            assert len(orderbook_2x2.get_orders_by_action(test_order_action)) == count
        else:
            assert len(orderbook_2x2.get_orders_by_action(test_order_action)) == 0

    @pytest.mark.parametrize("test_order_action,count,is_it_positive_case", [
        (OrderAction.BUY, 1, True), (OrderAction.SELL, 1, True), ('buy', 0, False),
        ('sell', 0, False), ('BUY', 0, False), ('SELL', 0, False), (OrderAction, 0, False),
        (OrderAction.BUY, 0.5, False)
    ])
    def test_get_order_by_action__check_limit_count(self, test_order_action, count, is_it_positive_case, symbol1, orderbook_2x2):
        """
        @description:
        Here we would like to make sure that client can define the count of orders during filering by action

        @pre-conditions:
        1. Create symbol (symbol1)
        2. Create order book (orderbook_2x2)

        @parameters:
        test_order_action: valid/invalid data that we would like to put to order as action
        count: expected count of orders by some order action
        is_it_positive_case: flag. "True" value means that test_order_action and count are valid and test should be passed.
                             "False" value means that test_order_action and count are invalid and test shouldn't be passed

        @steps:
        1. Create 2 BUY order
        2. Create 2 SELL order
        3. Place all created orders

        @assertions:
        1. If test_order_action is valid that count of orders by this action is correct
        2. If test_order_action is invalid that client received empty list
        """
        order1 = MarketOrder(symbol1, 0.25, OrderAction.BUY)
        order2 = MarketOrder(symbol1, 1, OrderAction.SELL)
        order3 = MarketOrder(symbol1, 1, OrderAction.SELL)
        order4 = MarketOrder(symbol1, 0.25, OrderAction.BUY)
        orderbook_2x2.place_order(order1)
        orderbook_2x2.place_order(order2)
        orderbook_2x2.place_order(order3)
        orderbook_2x2.place_order(order4)
        if is_it_positive_case:
            assert len(orderbook_2x2.get_orders_by_action(test_order_action, count)) == count
        else:
            assert len(orderbook_2x2.get_orders_by_action(test_order_action, count)) == 0

    def test_reject_order(self, market_buy_order, orderbook_2x2):
        """
        @description:
        Here we would like to make sure that client can reject the order

        @pre-conditions:
        1. Create order (market_buy_order)
        2. Create order book (orderbook_2x2)

        @steps:
        1. Place order
        2. Reject order

        @assertions:
        Order's status is changed to "REJECT"
        """
        orderbook_2x2.place_order(market_buy_order)
        orderbook_2x2.reject_order(market_buy_order)
        assert market_buy_order.status == OrderStatus.REJECT

    def test_fill_order(self, market_buy_order, orderbook_2x2):
        """
        @description:
        Here we would like to make sure that client can fill the order

        @pre-conditions:
        1. Create order (market_buy_order)
        2. Create order book (orderbook_2x2)

        @steps:
        1. Place order
        2. Fill order

        @assertions:
        Order's status is changed to "FILL"
        """
        orderbook_2x2.place_order(market_buy_order)
        orderbook_2x2.fill_order(market_buy_order)
        assert market_buy_order.status == OrderStatus.FILL

    def test_cancel_order(self, market_buy_order, orderbook_2x2):
        """
        @description:
        Here we would like to make sure that client can cancel the order

        @pre-conditions:
        1. Create order (market_buy_order)
        2. Create order book (orderbook_2x2)

        @steps:
        1. Place order
        2. Cancel order

        @assertions:
        Order's status is changed to "CANCEL"
        """
        orderbook_2x2.place_order(market_buy_order)
        orderbook_2x2.cancel_order(market_buy_order)
        assert market_buy_order.status == OrderStatus.CANCEL

    def test_get_order_by_id(self, market_buy_order, orderbook_2x2):
        """
        @description:
        Here we would like to make sure that client can get order by id

        @pre-conditions:
        1. Create order (market_buy_order)
        2. Create order book (orderbook_2x2)

        @steps:
        1. Place order
        2. Reject order

        @assertions:
        Order's status is changed to "REJECT"
        """
        orderbook_2x2.place_order(market_buy_order)
        assert orderbook_2x2.get_order_by_id(market_buy_order.id) == market_buy_order

    def test_get_market_data(self, symbol1, orderbook_2x2):
        """
        @description:
        Here we would like to make sure that client can get market data

        @pre-conditions:
        1. Create symbol (symbol1)
        2. Create order book (orderbook_2x2)

        @steps:
        1. Create 2 orders
        2. Place orders
        3. Get market data

        @assertions:
        JSON schema is valid
        All orders with action BUY in asks
        All orders with action SELL in bids
        Asks and Bids are sorted
        """
        order1 = MarketOrder(symbol1, 0.25, OrderAction.BUY)
        order2 = MarketOrder(symbol1, 0.25, OrderAction.BUY)
        order3 = MarketOrder(symbol1, 0.25, OrderAction.SELL)
        order4 = MarketOrder(symbol1, 0.25, OrderAction.SELL)
        orderbook_2x2.place_order(order1)
        orderbook_2x2.place_order(order2)
        orderbook_2x2.place_order(order3)
        orderbook_2x2.place_order(order4)
        market_data: dict = orderbook_2x2.get_market_data()

        assert is_market_data_schema_valid(market_data)

        asks = orderbook_2x2.get_orders_by_action(OrderAction.BUY)
        bids = orderbook_2x2.get_orders_by_action(OrderAction.SELL)
        assert {'price': order1.price, 'quantity': order1.quantity} in market_data['asks']
        assert {'price': order2.price, 'quantity': order2.quantity} in market_data['asks']
        assert {'price': order3.price, 'quantity': order3.quantity} in market_data['bids']
        assert {'price': order4.price, 'quantity': order4.quantity} in market_data['bids']

        assert market_data['bids'][0]['price'] >= market_data['bids'][1]['price']
        assert market_data['asks'][0]['price'] >= market_data['asks'][1]['price']


class TestOrderBookDeep:
    @pytest.mark.parametrize("test_deep,is_it_positive_case", [
        ([0, 0], True), ([1, 1], True), ([-1, -1], False),
        ([None, None], False), ([True, 1], False), (['A', 0], False),
        ([..., ...], False), ([pow(2, 2048), pow(2, 2048)], True), ([(1, 2), (1, 4)], False),
        ([int, 1], False)
    ])
    def test_deep_values(self, test_deep, is_it_positive_case):
        """
            @description:
            Here we would like to check how OrderBook can validate the incoming Deep parameter

            @parameters:
            test_deep: valid/invalid data that we would like to put to deep
            is_it_positive_case: flag. "True" value means that test_deep is valid and test should be passed.
                             "False" value means that test_deeo is invalid and test shouldn't be passed

            @steps:
            1. Create deep
            2. Create order book by using created deep

            @assertions:
            1. If test case is invalid then order book shouldn't be created and client should receive the error
               message like "The deep {deep} is not valid. Probably, asks_count or bids_count are les then 0. "
            2. If test case is valid then order book's deep should be equals to created deep
        """
        deep = Deep(test_deep[0], test_deep[1])
        order_book = None
        try:
            order_book = OrderBook(deep)
        except ChangeOrderBookDeepError as e:
            assert not is_it_positive_case
            assert e.msg == f"The deep {deep} is not valid. Probably, asks_count or bids_count are les then 0. "
        assert order_book.deep == deep if is_it_positive_case else order_book is None
