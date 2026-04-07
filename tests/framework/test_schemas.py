"""
Tests for the pandera DataFrame schemas.

These tests document the *contract* each loader enforces and demonstrate
what happens when data violates it — which is the whole point of having schemas.
"""

import pytest
import polars as pl
import pandera.errors

from otocyon.framework.schemas import OHLCVSchema, CryptoSchema, EquitySchema


# ---------------------------------------------------------------------------
# OHLCVSchema — base contract
# ---------------------------------------------------------------------------


def test_ohlcv_schema_passes_valid_data() -> None:
    df = pl.DataFrame({"close": [100.0, 101.5, 99.0]})
    validated = OHLCVSchema.validate(df)
    assert validated.shape == df.shape


def test_ohlcv_schema_rejects_missing_close_column() -> None:
    """A DataFrame without 'close' must fail immediately."""
    df = pl.DataFrame({"price": [100.0, 101.0]})
    with pytest.raises(pandera.errors.SchemaError):
        OHLCVSchema.validate(df)


def test_ohlcv_schema_rejects_non_positive_close() -> None:
    """Zero or negative close prices indicate corrupt / untransformed data."""
    df = pl.DataFrame({"close": [100.0, 0.0, -5.0]})
    with pytest.raises(pandera.errors.SchemaError):
        OHLCVSchema.validate(df)


def test_ohlcv_schema_rejects_null_close() -> None:
    """Null close prices must not silently propagate into feature calculations."""
    df = pl.DataFrame({"close": [100.0, None, 99.0]})
    with pytest.raises(pandera.errors.SchemaError):
        OHLCVSchema.validate(df)


def test_ohlcv_schema_allows_extra_columns() -> None:
    """strict=False — pre-computed feature columns in the parquet are fine."""
    df = pl.DataFrame({
        "close": [100.0, 101.0],
        "ma_20": [98.0, 99.0],
        "vol_20": [0.12, 0.11],
    })
    validated = OHLCVSchema.validate(df)
    assert "ma_20" in validated.columns


# ---------------------------------------------------------------------------
# CryptoSchema — extends OHLCV with optional volume
# ---------------------------------------------------------------------------


def test_crypto_schema_passes_with_volume() -> None:
    df = pl.DataFrame({
        "close": [50_000.0, 51_000.0],
        "volume": [1_200.0, 980.0],
    })
    CryptoSchema.validate(df)


def test_crypto_schema_passes_without_volume() -> None:
    """Volume is optional — some feeds omit it."""
    df = pl.DataFrame({"close": [50_000.0, 51_000.0]})
    CryptoSchema.validate(df)


def test_crypto_schema_rejects_negative_volume() -> None:
    """Negative volume is physically impossible — catches sign-flip bugs."""
    df = pl.DataFrame({
        "close": [50_000.0, 51_000.0],
        "volume": [1_200.0, -50.0],
    })
    with pytest.raises(pandera.errors.SchemaError):
        CryptoSchema.validate(df)


# ---------------------------------------------------------------------------
# EquitySchema — extends Crypto with required returns column
# ---------------------------------------------------------------------------


def test_equity_schema_passes_with_nullable_first_return() -> None:
    """The first bar has no prior close, so returns[0] is null — this is valid."""
    df = pl.DataFrame({
        "close": [100.0, 110.0, 121.0],
        "returns": [None, 0.1, 0.1],
    })
    EquitySchema.validate(df)


def test_equity_schema_rejects_missing_returns_column() -> None:
    """DuckDBLoader always adds 'returns'; its absence means the SQL broke."""
    df = pl.DataFrame({"close": [100.0, 110.0]})
    with pytest.raises(pandera.errors.SchemaError):
        EquitySchema.validate(df)
