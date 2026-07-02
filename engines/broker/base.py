"""
Broker Adapter Base -- Phase 22
Abstract interface that all concrete broker adapters must implement.
Only R/O methods exposed -- no order placement ever.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Holding:
    symbol:        str
    exchange:      str
    isin:          str
    qty:           int
    avg_cost:      float
    ltp:           float
    current_value: float
    pnl:           float
    pnl_pct:       float


@dataclass
class Position:
    symbol:   str
    exchange: str
    qty:      int       # net qty (negative = short)
    avg_cost: float
    ltp:      float
    pnl:      float
    product:  str       # CNC, MIS, NRML


@dataclass
class Trade:
    date:     str       # YYYY-MM-DD
    symbol:   str
    exchange: str
    action:   str       # BUY | SELL
    qty:      int
    price:    float
    order_id: str = ""


class BrokerAdapter(ABC):
    """Read-only broker interface. Concrete adapters: DhanAdapter, CsvAdapter."""

    @abstractmethod
    def ping(self) -> bool:
        """Returns True if credentials are valid and API is reachable."""

    @abstractmethod
    def get_holdings(self) -> list[Holding]:
        """Return all long-term equity holdings (delivery positions)."""

    @abstractmethod
    def get_positions(self) -> list[Position]:
        """Return open intraday / F&O positions for today."""

    @abstractmethod
    def get_trade_history(self, from_date: str, to_date: str) -> list[Trade]:
        """
        Return executed trades between from_date and to_date (YYYY-MM-DD).
        Used to bootstrap transactions.csv with real trade data.
        """
