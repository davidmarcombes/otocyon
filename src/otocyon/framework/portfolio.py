from typing import Any

from structlog.stdlib import BoundLogger
from .instrument import BaseInstrument
from .logger import NO_LOGGER

class Portfolio:
    """ Tracks positions and cash for the backtest. """
    def __init__(self, initial_cash: float = 100_000.0, ctx: Any = None):
        """
        Initialize the portfolio.

        Args:
            initial_cash: Starting cash balance for the portfolio. Defaults to 100,000.0.
            ctx: The shared configuration context.
        """
        self.ctx = ctx
        self._initial_cash = initial_cash
        self._cash = initial_cash
        self._positions: dict[str, float] = {}

    def logger(self) -> BoundLogger:
        """ Get the shared logger from context or use a fallback. """
        return getattr(self.ctx, "logger", NO_LOGGER)

    @property
    def cash(self) -> float:
        """ 
        The current available cash in the portfolio.
        
        Returns:
            Current cash balance.
        """
        return self._cash

    def get_quantity(self, symbol: str) -> float:
        """
        Get the current holding quantity of a specific instrument.

        Args:
            symbol: The instrument symbol.

        Returns:
            Current positional quantity, or 0.0 if not held.
        """
        return self._positions.get(symbol, 0.0)

    def set_position(self, instr: BaseInstrument, target_quantity: float) -> None:
        """ 
        Executes trades at the current market price to reach the target positional quantity.

        If the portfolio has insufficient cash to enter a position, it will block 
        the trade and log a warning. Returns early if the target quantity is already reached.

        Args:
            instr: The instrument to trade.
            target_quantity: The desired final quantity of the holding.
        """
        symbol = instr.symbol
        current_qty = self.get_quantity(symbol)
        diff = target_quantity - current_qty
        
        if diff == 0:
            return

        price = instr.price
        cost = diff * price
        
        if self._cash < cost:
            self.logger().warning(f"Insufficient cash to buy {diff} of {symbol}. "
                                   f"Required: {cost}, Have: {self._cash}")
            # Optional: Partial fill? For now, we block.
            return

        self._cash -= cost
        self._positions[symbol] = target_quantity
        
        direction = "BUY" if diff > 0 else "SELL"
        self.logger().info(f"[PORTFOLIO] {direction} {abs(diff)} {symbol} @ {price:.2f}. "
                            f"New Qty: {target_quantity}, Cash: {self._cash:.2f}")

    def get_equity(self, active_instruments: dict[str, BaseInstrument]) -> float:
        """ 
        Calculates the current net liquidation value (Cash + Position Values).

        Args:
            active_instruments: A dictionary of instruments loaded in the current simulation, 
                                containing the most recent pricing data.

        Returns:
            The total equity of the portfolio.
        """
        holdings_value = 0.0
        for symbol, qty in self._positions.items():
            if qty != 0:
                price = active_instruments[symbol].price
                holdings_value += qty * price
        return self._cash + holdings_value
