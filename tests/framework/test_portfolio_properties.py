"""
Property-based tests for Portfolio and the Signal / Indicator data structures.

Hypothesis generates hundreds of random inputs and checks that core invariants
hold for all of them — catching edge cases that hand-written examples miss.
"""

import pytest
from hypothesis import given, assume
from hypothesis import strategies as st

from otocyon.framework.portfolio import Portfolio
from otocyon.framework.instrument import BaseInstrument, BaseSpec
from otocyon.framework.signal import Signal
from otocyon.framework.indicator import Indicator


# ---------------------------------------------------------------------------
# Shared test double
# ---------------------------------------------------------------------------


class FixedPriceInstrument(BaseInstrument):
    """Instrument whose price is fixed at construction — no data loading."""

    def __init__(self, symbol: str, price: float) -> None:
        super().__init__(
            spec=BaseSpec(symbol=symbol, asset_class="mock"),
            loader=None,
            ctx=None,  # type: ignore[arg-type]
        )
        self._mock_price = price

    @property
    def price(self) -> float:
        return self._mock_price

    def get_type(self) -> str:
        return "mock"


# ---------------------------------------------------------------------------
# Portfolio invariants
# ---------------------------------------------------------------------------


@given(
    initial_cash=st.floats(min_value=1.0, max_value=1_000_000.0, allow_nan=False, allow_infinity=False),
    price=st.floats(min_value=0.01, max_value=10_000.0, allow_nan=False, allow_infinity=False),
    qty=st.floats(min_value=0.001, max_value=1_000.0, allow_nan=False, allow_infinity=False),
)
def test_equity_conserved_after_round_trip(initial_cash: float, price: float, qty: float) -> None:
    """
    Buying then selling at the same price must return total equity to
    its starting value (no slippage in the POC model).
    """
    assume(initial_cash >= price * qty)  # only test affordable trades

    portfolio = Portfolio(initial_cash=initial_cash)
    instr = FixedPriceInstrument("X", price)

    portfolio.set_position(instr, qty)   # buy
    portfolio.set_position(instr, 0.0)   # sell back to flat

    equity = portfolio.get_equity({"X": instr})
    assert abs(equity - initial_cash) < 1e-6, (
        f"Expected equity={initial_cash}, got {equity} "
        f"(price={price}, qty={qty})"
    )


@given(
    initial_cash=st.floats(min_value=1.0, max_value=1_000_000.0, allow_nan=False, allow_infinity=False),
    price=st.floats(min_value=0.01, max_value=10_000.0, allow_nan=False, allow_infinity=False),
    qty=st.floats(min_value=0.001, max_value=1_000.0, allow_nan=False, allow_infinity=False),
)
def test_cash_decreases_by_exact_cost_on_buy(initial_cash: float, price: float, qty: float) -> None:
    """Cash must decrease by exactly price × qty on a successful buy."""
    assume(initial_cash >= price * qty)

    portfolio = Portfolio(initial_cash=initial_cash)
    instr = FixedPriceInstrument("X", price)
    portfolio.set_position(instr, qty)

    expected_cash = initial_cash - price * qty
    assert abs(portfolio.cash - expected_cash) < 1e-6


@given(
    initial_cash=st.floats(min_value=0.01, max_value=999.0, allow_nan=False, allow_infinity=False),
    price=st.floats(min_value=1000.0, max_value=100_000.0, allow_nan=False, allow_infinity=False),
)
def test_insufficient_cash_leaves_state_unchanged(initial_cash: float, price: float) -> None:
    """
    Attempting a trade that exceeds available cash must not modify any state.
    """
    portfolio = Portfolio(initial_cash=initial_cash)
    instr = FixedPriceInstrument("X", price)

    portfolio.set_position(instr, 1.0)  # always unaffordable given the ranges above

    assert portfolio.cash == initial_cash
    assert portfolio.get_quantity("X") == 0.0


@given(
    initial_cash=st.floats(min_value=10_000.0, max_value=1_000_000.0, allow_nan=False, allow_infinity=False),
    price=st.floats(min_value=1.0, max_value=1_000.0, allow_nan=False, allow_infinity=False),
    qty=st.floats(min_value=0.001, max_value=100.0, allow_nan=False, allow_infinity=False),
)
def test_equity_never_negative(initial_cash: float, price: float, qty: float) -> None:
    """Total portfolio equity must never go negative for long-only positions."""
    assume(initial_cash >= price * qty)

    portfolio = Portfolio(initial_cash=initial_cash)
    instr = FixedPriceInstrument("X", price)
    portfolio.set_position(instr, qty)

    equity = portfolio.get_equity({"X": instr})
    assert equity >= 0.0


# ---------------------------------------------------------------------------
# Signal contracts
# ---------------------------------------------------------------------------


@given(
    symbol=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="-")),
    weight=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    side=st.sampled_from(["LONG", "SHORT", "FLAT"]),
)
def test_signal_is_active_until_cancelled(symbol: str, weight: float, side: str) -> None:
    """A freshly created signal must always be active."""
    sig = Signal(symbol=symbol, weight=weight, side=side)
    assert sig.is_active is True


@given(
    symbol=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="-")),
    weight=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    side=st.sampled_from(["LONG", "SHORT", "FLAT"]),
    reason=st.text(max_size=100),
)
def test_cancel_is_idempotent(symbol: str, weight: float, side: str, reason: str) -> None:
    """Calling cancel() multiple times must not raise and must stay inactive."""
    sig = Signal(symbol=symbol, weight=weight, side=side)
    sig.cancel(reason)
    sig.cancel(reason)  # second call must be safe
    assert sig.is_active is False


# ---------------------------------------------------------------------------
# Indicator contracts
# ---------------------------------------------------------------------------


@given(
    name=st.text(min_size=1, max_size=50),
    value=st.one_of(
        st.floats(allow_nan=False, allow_infinity=False),
        st.integers(),
        st.text(max_size=20),
    ),
    symbol=st.text(min_size=1, max_size=20),
)
def test_indicator_is_immutable(name: str, value, symbol: str) -> None:
    """Frozen Indicators must raise AttributeError on any field mutation."""
    ind = Indicator(name=name, value=value, symbol=symbol)
    with pytest.raises((AttributeError, TypeError)):
        ind.name = "mutated"  # type: ignore[misc]


def test_indicator_metadata_breaks_hashability() -> None:
    """
    Documents a known design trade-off found by hypothesis:

    ``Indicator`` carries a ``metadata: dict`` field.  Because ``dict`` is
    unhashable, any Indicator instance (including those with the default
    empty-dict) cannot be used as a set / dict key.  The struct is *immutable*
    (frozen=True prevents field re-assignment) but not *hashable*.

    If hashability is required, metadata should be changed to
    ``tuple[tuple[str, Any], ...]`` or ``None``.
    """
    ind = Indicator(name="RSI", value=42.0, symbol="BTC-USDT")
    with pytest.raises(TypeError, match="unhashable"):
        hash(ind)
