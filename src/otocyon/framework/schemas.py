"""
DataFrame Schemas
=================

Pandera schemas define the *contract* that loader output must satisfy before it
enters the framework.  Validation runs once at load time — catching bad column
names, wrong dtypes, out-of-range prices, or missing fields before they
silently corrupt downstream feature calculations.

Hierarchy::

    OHLCVSchema          ← minimum viable market bar (just a close price)
        └── CryptoSchema ← adds optional volume, used by PolarsLoader
            └── EquitySchema ← adds required returns column, used by DuckDBLoader

Usage::

    from otocyon.framework.schemas import CryptoSchema
    validated_df = CryptoSchema.validate(raw_df)   # raises SchemaError on failure

Swap ``strict=True`` in Config if you want to *reject* DataFrames that carry
columns not declared in the schema (useful for tightening prod pipelines).
"""

from typing import Optional

import pandera.polars as pa


class OHLCVSchema(pa.DataFrameModel):
    """
    Minimum viable market-data contract: a positive closing price.

    All other columns (pre-computed features, identifiers, timestamps) are
    permitted because ``strict=False`` — this schema only asserts what it
    *knows* must be true, not what must *not* exist.
    """

    close: float = pa.Field(
        gt=0,
        nullable=False,
        description="Closing price — must exist and be strictly positive.",
    )

    class Config:
        strict = False   # extra columns (pre-computed features, etc.) are fine
        coerce = False   # refuse to silently cast wrong types; fail loudly


class CryptoSchema(OHLCVSchema):
    """
    Schema for crypto OHLCV data produced by ``PolarsLoader``.

    Volume is optional (some crypto feeds omit it) but must be non-negative
    when present.
    """

    # Optional[float] is how pandera signals the column need not be present.
    # ge=0 + nullable=True apply when the column exists: no negatives, nulls ok.
    volume: Optional[float] = pa.Field(
        ge=0,
        nullable=True,
        description="Trade volume — optional, non-negative when present.",
    )


class EquitySchema(CryptoSchema):
    """
    Schema for equity data produced by ``DuckDBLoader``.

    The SQL window function always adds a ``returns`` column; the first row is
    null (no prior close to compare against), so ``nullable=True`` is required.
    """

    returns: float = pa.Field(
        nullable=True,
        description="Lag-1 percentage return — null for the first bar.",
    )
