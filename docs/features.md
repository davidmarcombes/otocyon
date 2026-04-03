# Feature Library

The `features` module provides a structured vocabulary for declaring what data a strategy
needs from each instrument. It enforces a clean separation between **where** data comes
from and **how** it is consumed.

Import it alongside your specs:

```python
from ..framework import features, CryptoSpec, EquitySpec
```

---

## The Three Categories

### Category 1 – Column References (`features.col`)

Use when the column **already exists** in the loaded data — either pre-calculated by the
data-generation script or added by the loader's SQL query.

```python
aapl: EquityInstrument = EquitySpec(
    symbol="AAPL",
    features={
        "ma_20":  features.col("ma_20"),   # written by generate_data.py
        "vol_20": features.col("vol_20"),  # written by generate_data.py
        "returns": features.col("returns"), # added by DuckDBLoader SQL
    },
)
```

::: otocyon.framework.features.col
    options:
      show_root_heading: true

---

### Category 2 – Predefined Framework Routines

Use for **common technical-analysis calculations** that are shared across many strategies.
These are pure Polars expressions compiled in a single batch before the simulation starts.

```python
btc: CryptoInstrument = CryptoSpec(
    symbol="BTC-USDT",
    features={
        "ma_5":   features.sma("close", 5),
        "rsi_14": features.rsi("close", 14),
        "vol_20": features.volatility("close", 20),
    },
)
```

::: otocyon.framework.features.sma
    options:
      show_root_heading: true

::: otocyon.framework.features.ema
    options:
      show_root_heading: true

::: otocyon.framework.features.volatility
    options:
      show_root_heading: true

::: otocyon.framework.features.returns
    options:
      show_root_heading: true

::: otocyon.framework.features.log_returns
    options:
      show_root_heading: true

::: otocyon.framework.features.momentum
    options:
      show_root_heading: true

::: otocyon.framework.features.rsi
    options:
      show_root_heading: true

::: otocyon.framework.features.bollinger_upper
    options:
      show_root_heading: true

::: otocyon.framework.features.bollinger_lower
    options:
      show_root_heading: true

::: otocyon.framework.features.vwap
    options:
      show_root_heading: true

::: otocyon.framework.features.z_score
    options:
      show_root_heading: true

---

### Category 3 – Inline Custom Expressions

Use for **one-off calculations** that are too specific to deserve a named routine in the
framework. Pass raw Polars expressions directly in the `features` dict.

```python
eth: CryptoInstrument = CryptoSpec(
    symbol="ETH-USDT",
    features={
        "mom": features.momentum("close", 1),
        # Raw inline expression – not worth a shared name:
        "vol_ratio": pl.col("close").rolling_std(window_size=5)
                   / pl.col("close").rolling_std(window_size=20),
    },
)
```

---

## Accessing Features in the Strategy Loop

All compiled features are accessed via Python attribute syntax directly on the instrument
instance. The `__getattr__` fallback on `BaseInstrument` routes unknown attributes through
to the underlying Polars DataFrame at the current simulation cursor:

```python
@on_data()
def handle_market_data(self):
    yield [
        Indicator("AAPL-MA20",  self.aapl.ma_20,    "AAPL"),
        Indicator("BTC-RSI14",  self.btc.rsi_14,    "BTC-USDT"),
        Indicator("ETH-Mom",    self.eth.mom,        "ETH-USDT"),
    ]
```

> [!NOTE]
> `self.aapl.ma_20` is a **row-level scalar** (a Python float), not a Series. The cursor
> is advanced by the Engine on every time step so the value is always "current".
