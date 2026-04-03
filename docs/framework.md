# Framework

The framework module contains the core components and data structures that strategies use to discover data, yield indicators, and formulate signals.

## Core Data Structures

::: otocyon.framework.context.Context
    options:
      show_root_heading: true

::: otocyon.framework.indicator.Indicator
    options:
      show_root_heading: true

::: otocyon.framework.signal.Signal
    options:
      show_root_heading: true

## Portfolio Management

::: otocyon.framework.portfolio.Portfolio
    options:
      show_root_heading: true

## Registry & Decorators

::: otocyon.framework.decorators
    options:
      members:
        - strategy
        - on_data
        - on_indicator
      show_root_heading: true

::: otocyon.framework.registry.Registry
    options:
      show_root_heading: true

## Market & Factories

::: otocyon.framework.market.Market
    options:
      show_root_heading: true

::: otocyon.framework.instrument_factory.InstrumentFactory
    options:
      show_root_heading: true
