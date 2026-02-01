"""
QuantConnect Algorithm: RSI Momentum Strategy
Simplified from RichesReach AI Trading Platform
Generated: 2026-02-01T19:41:18.959982

This algorithm implements a clean RSI-based momentum strategy.
Entry: RSI < 30 (oversold). Exit: RSI > 70 (overbought).
"""

from AlgorithmImports import *

class RSIMomentumStrategy(QCAlgorithm):
    def Initialize(self):
        self.SetStartDate(2020, 1, 1)
        self.SetEndDate(2023, 12, 31)
        self.SetCash(100000)

        # Set benchmark
        self.SetBenchmark("SPY")

        # Symbols to trade
        self.symbols = ["SPY", "AAPL", "MSFT", "GOOGL"]

        # Add equities and RSI only
        self.rsi = {}
        for symbol in self.symbols:
            self.AddEquity(symbol, Resolution.DAILY)
            self.rsi[symbol] = self.RSI(symbol, 14)

        # Strategy parameters
        self.rsi_oversold = 30
        self.rsi_overbought = 70
        self.position_size = 0.25  # 25% per symbol

    def OnData(self, data):
        for symbol in self.symbols:
            if symbol not in data or not data[symbol]:
                continue

            if not self.rsi[symbol].IsReady:
                continue

            rsi_value = self.rsi[symbol].Current.Value

            # Entry: RSI oversold only
            if not self.Portfolio[symbol].Invested:
                if rsi_value < self.rsi_oversold:
                    self.SetHoldings(symbol, self.position_size)

            # Exit: RSI overbought only
            else:
                if rsi_value > self.rsi_overbought:
                    self.Liquidate(symbol)
