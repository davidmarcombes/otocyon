# Otocyon 🦊

A modern, declarative strategy backtesting framework built on the **"Bucket Brigade"** architecture.

## 🚀 Architecture: The Bucket Brigade

Otocyon separates detection, logic, and execution into a clean, multi-pass pipeline:

1.  **Sensor Pass (`@on_data`)**: Strategies consume raw market data and yield `Indicator` objects.
2.  **Middleware Pass**: The engine aggregates indicators, calculates meta-metrics (e.g., average price across a universe), and builds a global indicator pool.
3.  **Brain Pass (`@on_indicator`)**: Strategies listen to the global pool and yield `Signal` objects (intents).
4.  **Muscle Pass (`Portfolio`)**: The engine resolves signals and executes trades, managing position rebalancing seamlessly.

## 🛠 Features

-   **Zero-Boilerplate API**: Instruments are automatically injected into your strategy instance using the unified `@strategy` decorator.
-   **Lazy Statistics Engine**: Compute and cache stats on the fly or load them natively out-of-core.
-   **Pluggable Loaders**: Seamlessly switch your data pipeline between Mocked data, Polars (Fast Parquet), and DuckDB sources.
-   **Shared Thread Context**: State is isolated in a shared container accessible securely across all strategies.

Ready to build? Dive into the [Engine](engine.md) or check out the [Framework Data Structures](framework.md).
