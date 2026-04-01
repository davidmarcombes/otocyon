from ..framework import (
    NO_LOGGER,
    strategy, on_data, on_setup,
    InstrumentFactory,
    CryptoSpec,  
)

@strategy("BTC-ETH-TrendFollower", universe=["BTC-USDT", "ETH-USDT"])
class TrendFollower:
    def __init__(self, ctx):
        self.ctx = ctx
        self.lookback = 20
        self.btc = None
        self.eth = None
        
    def logger(self):
        return self.ctx.logger if (self.ctx and self.ctx.logger) else NO_LOGGER 
        
    @on_setup()
    def setup(self):
        """
        This method is called once at the start. You can initialize state here.
        """
        self.logger().info("Setting up BTC ETH TrendFollower strategy.")
        factory = InstrumentFactory(self.ctx)
        self.btc = factory.create(CryptoSpec(symbol="BTC-USDT"))
        self.eth = factory.create(CryptoSpec(symbol="ETH-USDT"))

    @on_data()
    def handle_market_data(self):
        """
        This method is discovered by the Runner because of the decorator.
        """
        if self.btc is None or self.eth is None:
            raise ValueError("Instruments not initialized. Did you forget to call setup()?")
        
        btc_price = self.btc.price
        eth_price = self.eth.price
        
        self.logger().info(f"BTC Price: {btc_price}, ETH Price: {eth_price}")   
        
        # TODO: Implement your trend-following logic here. 
        
        # TODO: Emit signal