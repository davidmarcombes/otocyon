# Engine

The `Engine` class runs the simulation.

## Lifecycle

```python
engine = Engine(ctx)
engine.add_strategies()   # or add_strategies(names=["MyStrategy"])
engine.prepare()          # compiles features, calls @on_setup handlers
engine.run()              # executes the simulation loop
```

**`add_strategies`** reads from `REGISTRY`, instantiates each strategy class, creates instruments for its universe, and injects them as named attributes on the instance.

**`prepare`** scans strategy methods for decorated handlers, calls `@on_setup` handlers once, then calls `compile_features()` on every instrument. Feature compilation runs all declared Polars expressions in a single batch — one pass over the full DataFrame per instrument.

**`run`** iterates from bar 25 (warm-up skip) to the end of the data. Each bar:

1. Syncs all instrument cursors to the current index.
2. Calls each `@on_data` handler and collects the yielded `Indicator` objects into `indicators_pool`.
3. Computes the universe average price as a meta-indicator (`AVG-Price`).
4. Calls each `@on_indicator` handler with `indicators_pool` and collects yielded `Signal` objects.
5. For each active signal, converts the weight to a target quantity using current portfolio equity, then calls `portfolio.set_position` if the quantity delta exceeds `1e-6`.

::: otocyon.engine.engine.Engine
    options:
      show_root_heading: true
      members:
        - __init__
        - add_strategies
        - add_strategy
        - prepare
        - run
