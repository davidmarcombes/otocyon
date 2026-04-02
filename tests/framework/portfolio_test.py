import pytest
from otocyon.framework.portfolio import Portfolio
from otocyon.framework.instrument import BaseInstrument, BaseSpec

class MockInstrument(BaseInstrument):
    def __init__(self, symbol: str, price: float):
        super().__init__(spec=BaseSpec(symbol=symbol, asset_class="mock"), loader=None, ctx=None)
        self._mock_price = price

    @property
    def price(self) -> float:
        return self._mock_price

    def get_type(self) -> str:
        return "mock"

def test_portfolio_basic_usage():
    """
    Shows how the Portfolio manages cash, tracks positions,
    and executes trades via `set_position`.
    """
    # 1. Initialize portfolio with starting cash
    portfolio = Portfolio(initial_cash=10000.0)
    
    # 2. Setup mock instruments
    aapl = MockInstrument("AAPL", 150.0)
    
    # 3. Buy 10 shares of AAPL
    portfolio.set_position(aapl, 10.0)
    
    # Verify cash decreased by cost (10 * 150 = 1500)
    assert portfolio.cash == 8500.0
    assert portfolio.get_quantity("AAPL") == 10.0
    
    # 4. Sell 5 shares of AAPL (target position = 5)
    portfolio.set_position(aapl, 5.0)
    
    # Verify cash increased by proceeds (5 * 150 = 750)
    assert portfolio.cash == 9250.0
    assert portfolio.get_quantity("AAPL") == 5.0
    
    # 5. Measure total equity (Cash + Value of Assets)
    active_instruments = {"AAPL": aapl}
    total_equity = portfolio.get_equity(active_instruments)
    
    # Total Equity = 9250 Cash + (5 * 150) API = 10000.0
    assert total_equity == 10000.0

def test_portfolio_insufficient_cash():
    """
    Shows what happens when Portfolio doesn't have enough cash
    to open a position.
    """
    portfolio = Portfolio(initial_cash=100.0)
    aapl = MockInstrument("AAPL", 150.0)
    
    # Try to buy 1 share of AAPL, but short on cash
    portfolio.set_position(aapl, 1.0)
    
    # Cash shouldn't change, position shouldn't be added
    assert portfolio.cash == 100.0
    assert portfolio.get_quantity("AAPL") == 0.0
