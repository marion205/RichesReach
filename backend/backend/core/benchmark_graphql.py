import graphene
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class BenchmarkDataPoint(graphene.ObjectType):
    """Single data point for benchmark performance"""
    timestamp = graphene.String(description="ISO timestamp of the data point")
    value = graphene.Float(description="Benchmark value at this timestamp")
    change = graphene.Float(description="Change from previous point")
    changePercent = graphene.Float(description="Percentage change from previous point")

class BenchmarkSeries(graphene.ObjectType):
    """Complete benchmark series for a timeframe"""
    symbol = graphene.String(description="Benchmark symbol (e.g., SPY, QQQ)")
    name = graphene.String(description="Human-readable benchmark name")
    timeframe = graphene.String(description="Timeframe (1D, 1W, 1M, 3M, 1Y, All)")
    dataPoints = graphene.List(BenchmarkDataPoint, description="Array of data points")
    startValue = graphene.Float(description="Starting value of the series")
    endValue = graphene.Float(description="Ending value of the series")
    totalReturn = graphene.Float(description="Total return for the period")
    totalReturnPercent = graphene.Float(description="Total return percentage for the period")
    volatility = graphene.Float(description="Volatility (standard deviation) of returns")

class BenchmarkQuery(graphene.ObjectType):
    """GraphQL queries for benchmark data"""
    
    benchmarkSeries = graphene.Field(
        BenchmarkSeries,
        symbol=graphene.String(required=True, description="Benchmark symbol (SPY, QQQ, etc.)"),
        timeframe=graphene.String(required=True, description="Timeframe (1D, 1W, 1M, 3M, 1Y, All)"),
        description="Get benchmark performance data for a specific symbol and timeframe"
    )
    
    availableBenchmarks = graphene.List(
        graphene.String,
        description="Get list of available benchmark symbols"
    )

    def resolve_benchmarkSeries(self, info, symbol: str, timeframe: str):
        """Resolve benchmark series data"""
        try:
            from .benchmark_service import BenchmarkService
            benchmark_service = BenchmarkService()
            
            # Validate timeframe
            valid_timeframes = ['1D', '1W', '1M', '3M', '1Y', 'All']
            if timeframe not in valid_timeframes:
                raise ValueError(f"Invalid timeframe: {timeframe}. Must be one of {valid_timeframes}")
            
            # Get benchmark data
            series_data = benchmark_service.get_benchmark_series(symbol, timeframe)
            
            if not series_data:
                logger.warning(f"No benchmark data found for {symbol} {timeframe}")
                return None
                
            return BenchmarkSeries(
                symbol=series_data['symbol'],
                name=series_data['name'],
                timeframe=timeframe,
                dataPoints=[
                    BenchmarkDataPoint(
                        timestamp=point['timestamp'],
                        value=point['value'],
                        change=point.get('change', 0),
                        changePercent=point.get('changePercent', 0)
                    ) for point in series_data['dataPoints']
                ],
                startValue=series_data['startValue'],
                endValue=series_data['endValue'],
                totalReturn=series_data['totalReturn'],
                totalReturnPercent=series_data['totalReturnPercent'],
                volatility=series_data.get('volatility', 0)
            )
            
        except Exception as e:
            logger.error(f"Error resolving benchmark series for {symbol} {timeframe}: {e}")
            return None

    def resolve_availableBenchmarks(self, info):
        """Resolve list of available benchmark symbols"""
        return ['SPY', 'QQQ', 'IWM', 'VTI', 'VEA', 'VWO', 'AGG', 'TLT', 'GLD', 'SLV']
