from dataclasses import dataclass


@dataclass
class Deep:
    """
    This class characterizes the order book's deep (how much asks and bids should be visible in order book)
    """
    ask_count: int
    bid_count: int
