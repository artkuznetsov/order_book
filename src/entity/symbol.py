from dataclasses import dataclass
from uuid import uuid4

from src.enums import SymbolType, Currency


@dataclass
class Symbol:
    """
    This class contains the symbol's data
    """
    name: str
    exchange: str
    type: SymbolType
    currency: Currency
    is_enabled: bool = True
    id: uuid4 = uuid4()