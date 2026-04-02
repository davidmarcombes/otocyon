import polars as pl
import numpy as np
import os

def generate_sample_data(symbol, asset_class, n=100):
    np.random.seed(42 if symbol == "BTC-USDT" else 123)
    start_price = 100.0 if asset_class == "crypto" else 200.0
    returns = np.random.normal(0, 0.01, n)
    prices = start_price * np.exp(np.cumsum(returns))
    
    from datetime import datetime, timedelta
    start_dt = datetime(2024, 1, 1)
    end_dt = start_dt + timedelta(days=n-1)

    df = pl.DataFrame({
        "timestamp": pl.datetime_range(start=start_dt, end=end_dt, interval="1d", eager=True),
        "close": prices,
        "volume": np.random.uniform(100, 1000, n)
    })
    
    if asset_class == "equity":
        # Pre-calculated stats for equities
        df = df.with_columns([
            pl.col("close").rolling_mean(window_size=20).alias("ma_20"),
            pl.col("close").rolling_std(window_size=20).alias("vol_20")
        ])

    # Store in data/{asset_class}/{symbol}.parquet
    dir_path = os.path.join("data", asset_class)
    os.makedirs(dir_path, exist_ok=True)
    path = os.path.join(dir_path, f"{symbol}.parquet")
    df.write_parquet(path)
    print(f"Generated {path}")

if __name__ == "__main__":
    # Cryptos
    generate_sample_data("BTC-USDT", "crypto")
    generate_sample_data("ETH-USDT", "crypto")
    
    # Equities
    generate_sample_data("AAPL", "equity")
    generate_sample_data("MSFT", "equity")
