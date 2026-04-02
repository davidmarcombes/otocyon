from dataclasses import dataclass, field
from functools import cached_property
import logging
from typing import Any, Dict
import duckdb
from .logger import NO_LOGGER

    
@dataclass(frozen=True)  # Frozen makes it immutable and thread-safe
class Context:
    """
    The Context object is a thread-safe container for runtime information.
    It is passed to every Strategy instance during execution.
    """
    
    logger: logging.Logger = NO_LOGGER # Common logger
    data_root: str = "data"  # Root data directory
    duckdb_path: str = ":memory:"  # Default to in-memory DuckDB
    config_file: str = "config.yaml"  # Path to config file
    metadata: dict = field(default_factory=dict)
    instruments: Dict[str, Any] = field(default_factory=dict)
    
    @cached_property
    def portfolio(self):
        from .portfolio import Portfolio
        return Portfolio(ctx=self)

    @cached_property
    def factory(self):
        from .instrument_factory import InstrumentFactory
        return InstrumentFactory(self)

    @cached_property
    def market(self):
        from .market import Market
        return Market()

    @cached_property
    def duckdb_connection(self) -> duckdb.DuckDBPyConnection:
        self.logger.debug("Connecting to DuckDB")
        conn = duckdb.connect(self.duckdb_path or ":memory:")
        conn.execute(f"SET home_directory='{self.data_root}'")
        return conn
    
    @cached_property
    def config(self) -> Dict[str, Any]:
        if self.config_file:
            if self.config_file.endswith(".yaml") or self.config_file.endswith(".yml"):
                self.logger.debug(f"Loading YAML config from {self.config_file}")
                from ruamel.yaml import YAML
                yaml = YAML(typ='safe')
                with open(self.config_file, 'r') as f:
                    return yaml.load(f)
            elif self.config_file.endswith(".json"):
                self.logger.debug(f"Loading JSON config from {self.config_file}")
                import json
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            elif self.config_file.endswith(".toml"):
                self.logger.debug(f"Loading TOML config from {self.config_file}")
                import tomllib
                with open(self.config_file, 'rb') as f:
                    return tomllib.load(f)
            else:
                self.logger.warning(f"Unknown config file type: {self.config_file}")
                return {}
        else:
            self.logger.warning("No config file specified") 
        return {}
        

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # This runs even if the backtest crashes!
        # Access the internal dict since it's a cached_property
        if 'duckdb_connection' in self.__dict__:
            self.logger.info("Closing DuckDB Connection...")
            self.duckdb_connection.close()    