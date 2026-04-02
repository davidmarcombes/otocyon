from typing import Dict, Any
from .instrument import BaseInstrument
from .logger import NO_LOGGER

class Portfolio:
    """ Tracks positions and cash for the backtest. """
    def __init__(self, initial_cash: float = 100_000.0, ctx: Any = None):
        self.ctx = ctx
        self._initial_cash = initial_cash
        self._cash = initial_cash
        self._positions: Dict[str, float] = {}

    def logger(self):
        return getattr(self.ctx, "logger", NO_LOGGER)

    @property
    def cash(self) -> float:
        return self._cash

    def get_quantity(self, symbol: str) -> float:
        return self._positions.get(symbol, 0.0)

    def set_position(self, instr: BaseInstrument, target_quantity: float):
        """ Executes a trade at current price to reach target quantity. """
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

    def get_equity(self, active_instruments: Dict[str, BaseInstrument]) -> float:
        """ Calculates current net liquidation value. """
        holdings_value = 0.0
        for symbol, qty in self._positions.items():
            if qty != 0:
                price = active_instruments[symbol].price
                holdings_value += qty * price
        return self._cash + holdings_value
