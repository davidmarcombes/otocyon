from typing import Any

from ..framework import REGISTRY, Indicator, CryptoSpec
from ..framework.context import Context
from ..framework.instrument import BaseInstrument


class Engine:
    """
    The core execution engine of the Otocyon framework.

    The Engine manages the entire simulation lifecycle, orchestrating the
    "Bucket Brigade" pipeline. It discovers strategies, collects market data,
    computes global indicators, and executes trades across the portfolio.
    """

    def __init__(self, ctx: Context) -> None:
        """
        Initialize the Engine.

        Args:
            ctx: The shared context containing configuration and shared state.
        """
        self.ctx = ctx
        self.instruments: dict[str, BaseInstrument] = self.ctx.instruments
        self.strategies: list[Any] = []

    @property
    def factory(self) -> Any:
        return self.ctx.factory

    def add_strategies(self, names: list[str] | None = None) -> None:
        for strategy_item in REGISTRY.get_all().values():
            strategy_class = strategy_item["class"]
            if names is None or strategy_class._otocyon_name in names:
                self.add_strategy(strategy_class)

    def add_strategy(self, strategy_class: Any) -> None:
        """Discovers requirements from the items tagged in the class."""
        # 1. Pull the universe from the class metadata
        universe = getattr(strategy_class, "_otocyon_universe", [])

        # Normalize universe to a dictionary of {attr_name: spec}
        name_spec_map: dict[str, Any] = {}
        if isinstance(universe, list):
            for item in universe:
                spec = item if not isinstance(item, str) else CryptoSpec(symbol=item)
                # For lists, we don't naturally have an attribute name,
                # but we still ensure they are created in the context.
                name_spec_map[spec.symbol] = spec
        elif isinstance(universe, dict):
            for attr_name, item in universe.items():
                spec = item if not isinstance(item, str) else CryptoSpec(symbol=item)
                name_spec_map[attr_name] = spec

        # 2. Ensure instruments are created and stored
        for attr_name, spec in name_spec_map.items():
            if spec.symbol not in self.instruments:
                instr = self.factory.create(spec)
                self.instruments[spec.symbol] = instr

        # 3. Instantiate the strategy and HYDRATE it with instruments
        instance = strategy_class(self.ctx)

        # If universe was a dict, we inject the instruments as attributes
        if isinstance(universe, dict):
            for attr_name, spec in name_spec_map.items():
                setattr(instance, attr_name, self.instruments[spec.symbol])

        self.strategies.append(instance)

    def prepare(self) -> None:
        """Prepares for execution by finding decorators."""
        self.ctx.logger.info("Engine preparing for run...")
        self.setup_handlers: list[Any] = []
        self.data_handlers: list[Any] = []
        self.indicator_handlers: list[Any] = []

        for strat in self.strategies:
            # Inspect instance methods for decorators
            for attr_name in dir(strat):
                attr = getattr(strat, attr_name)
                if getattr(attr, "_is_setup_handler", False):
                    self.setup_handlers.append(attr)
                if getattr(attr, "_is_data_handler", False):
                    self.data_handlers.append(attr)
                if getattr(attr, "_is_indicator_handler", False):
                    self.indicator_handlers.append(attr)

        # Initial setup: call each setup handler once
        for handler in self.setup_handlers:
            handler()

        # Compile all requested declarative features across the universe
        self.ctx.logger.info("Engine compiling declarative instrument features...")
        for instr in self.instruments.values():
            instr.compile_features()

    def run(self) -> None:
        """Executes the simulation loop using the 'Bucket Brigade' pipeline."""
        self.ctx.logger.info("Engine starting run using Bucket Brigade pipeline...")
        if not self.instruments:
            self.ctx.logger.warning("No instruments found. Nothing to run!")
            return

        FIRST_INSTR = list(self.instruments.values())[0]
        max_len = len(FIRST_INSTR)

        # Warm-up period skip (minimal implementation)
        for i in range(25, max_len):
            self.ctx.logger.bind(step=i, max_steps=max_len).debug("engine.step")

            # --- 0. SYNC CURSORS ---
            for instr in self.instruments.values():
                instr._cursor = i

            # --- 1. SENSOR PASS (on_data) ---
            # Strategies consume data and YIELD a set/list of Indicators
            indicators_pool: dict[str, Indicator] = {}
            for handler in self.data_handlers:
                result = handler()
                if result:
                    # In python, yield makes a generator.
                    # If the user yielded a list or set, we unpack it.
                    for items in (result if hasattr(result, "__iter__") else [result]):
                        # If items is a list/set of Indicators
                        if isinstance(items, (list, set)):
                            for ind in items:
                                indicators_pool[ind.name] = ind
                        else:
                            # Assume it's a single Indicator
                            indicators_pool[items.name] = items

            # --- 2. MIDDLEWARE PASS (Meta-indicators) ---
            # Calculate average price across the universe as an example Meta-Indicator
            total_price = 0.0
            count = 0
            for ind in indicators_pool.values():
                if "Price" in ind.name:
                    total_price += ind.value
                    count += 1

            if count > 0:
                avg_price = total_price / count
                indicators_pool["AVG-Price"] = Indicator("AVG-Price", avg_price, "Universe")

            # --- 3. BRAIN PASS (on_indicator) ---
            # Strategies consume the global pool and YIELD Signals
            signals: list[Any] = []
            for handler in self.indicator_handlers:
                # We pass the pool as a dictionary (name: Indicator)
                results = handler(indicators_pool)
                if results:
                    # Collect all signals
                    for sig in (results if hasattr(results, "__iter__") else [results]):
                        signals.append(sig)

            # --- 4. MUSCLE PASS (Portfolio execution) ---
            # Resolve and execute signals. Minimal POC: execute all non-cancelled signals.
            for sig in signals:
                if sig.is_active:
                    if sig.symbol not in self.instruments:
                        self.ctx.logger.warning(f"Strategy sent signal for unknown symbol: {sig.symbol}")
                        continue
                    instr = self.instruments[sig.symbol]

                    # Convert weight to quantity (minimal implementation)
                    # Equity / Price * weight
                    current_equity = self.ctx.portfolio.get_equity(self.instruments)
                    target_qty = (current_equity / instr.price) * sig.weight

                    if sig.side == "SHORT":
                        target_qty *= -1.0
                    elif sig.side == "FLAT":
                        target_qty = 0.0

                    # FLOAT EPSILON CHECK: Avoid tiny trades
                    current_qty = self.ctx.portfolio.get_quantity(sig.symbol)
                    if abs(target_qty - current_qty) > 1e-6:
                        self.ctx.portfolio.set_position(instr, target_qty)

        self.ctx.logger.info("Engine finished run.")
