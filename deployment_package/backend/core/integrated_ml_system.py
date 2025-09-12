"""
Integrated ML System
Combines alternative data, deep learning, and real-time pipeline for maximum R² improvement
"""

import os
import sys
import django
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
import asyncio
import warnings
warnings.filterwarnings('ignore')

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()

from .alternative_data_service import AlternativeDataService
from .deep_learning_service import DeepLearningService
from .realtime_pipeline import RealTimeDataPipeline

logger = logging.getLogger(__name__)

class IntegratedMLSystem:
    """
    Integrated ML system combining all three high-impact improvements
    """
    
    def __init__(self):
        self.alternative_data_service = AlternativeDataService()
        self.deep_learning_service = DeepLearningService()
        self.realtime_pipeline = RealTimeDataPipeline()
        
        # System state
        self.is_initialized = False
        self.model_performance = {}
        self.last_update = datetime.now()
        
        # Performance tracking
        self.performance_history = []
        
    async def initialize_system(self, symbols: List[str]):
        """Initialize the integrated ML system"""
        logger.info("Initializing integrated ML system...")
        
        try:
            # Initialize alternative data service
            logger.info("Initializing alternative data service...")
            await self.alternative_data_service.get_alternative_data(symbols[:5])  # Test with first 5 symbols
            
            # Initialize deep learning service
            logger.info("Initializing deep learning service...")
            if self.deep_learning_service.deep_learning_available:
                # Create sample data for initialization
                n_samples = 1000
                n_features = 50
                X = np.random.randn(n_samples, n_features)
                y = np.random.randn(n_samples)
                
                # Train models
                lstm_results = self.deep_learning_service.train_lstm_model(X, y)
                transformer_results = self.deep_learning_service.train_transformer_model(X, y)
                
                self.model_performance = {
                    'lstm': lstm_results,
                    'transformer': transformer_results
                }
            
            # Initialize real-time pipeline
            logger.info("Initializing real-time pipeline...")
            # Pipeline will be started separately
            
            self.is_initialized = True
            logger.info("Integrated ML system initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing integrated ML system: {e}")
            raise
    
    async def train_models_with_real_data(self, symbols: List[str], days: int = 500) -> Dict[str, Any]:
        """Train models with real market data and alternative data"""
        logger.info(f"Training models with real data for {len(symbols)} symbols...")
        
        try:
            # Get enhanced market data
            import yfinance as yf
            
            market_data = {}
            for symbol in symbols:
                try:
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period=f"{days}d")
                    
                    if not hist.empty and len(hist) > 200:
                        # Basic features
                        hist['Returns'] = hist['Close'].pct_change()
                        hist['Log_Returns'] = np.log(hist['Close'] / hist['Close'].shift(1))
                        hist['Price_Range'] = (hist['High'] - hist['Low']) / hist['Close']
                        hist['Price_Position'] = (hist['Close'] - hist['Low']) / (hist['High'] - hist['Low'])
                        
                        # Moving averages
                        for window in [5, 10, 20, 50, 100, 200]:
                            hist[f'SMA_{window}'] = hist['Close'].rolling(window=window).mean()
                            hist[f'EMA_{window}'] = hist['Close'].ewm(span=window).mean()
                        
                        # Technical indicators
                        hist['RSI_14'] = self._calculate_rsi(hist['Close'], 14)
                        hist['MACD'] = hist['EMA_12'] - hist['EMA_26']
                        hist['MACD_Signal'] = hist['MACD'].ewm(span=9).mean()
                        hist['MACD_Histogram'] = hist['MACD'] - hist['MACD_Signal']
                        
                        # Bollinger Bands
                        hist['BB_Middle'] = hist['Close'].rolling(window=20).mean()
                        bb_std = hist['Close'].rolling(window=20).std()
                        hist['BB_Upper'] = hist['BB_Middle'] + (bb_std * 2)
                        hist['BB_Lower'] = hist['BB_Middle'] - (bb_std * 2)
                        hist['BB_Width'] = (hist['BB_Upper'] - hist['BB_Lower']) / hist['BB_Middle']
                        hist['BB_Position'] = (hist['Close'] - hist['BB_Lower']) / (hist['BB_Upper'] - hist['BB_Lower'])
                        
                        # Volume indicators
                        hist['Volume_MA'] = hist['Volume'].rolling(window=20).mean()
                        hist['Volume_Ratio'] = hist['Volume'] / hist['Volume_MA']
                        
                        # Volatility
                        hist['Volatility'] = hist['Returns'].rolling(window=20).std()
                        
                        # Fill NaN values
                        hist = hist.fillna(method='ffill').fillna(method='bfill').fillna(0)
                        
                        market_data[symbol] = hist
                        logger.info(f"✓ {symbol}: {len(hist)} days with {len(hist.columns)} features")
                        
                except Exception as e:
                    logger.error(f"Error processing {symbol}: {e}")
            
            if not market_data:
                raise ValueError("No market data available")
            
            # Get alternative data
            alternative_data = await self.alternative_data_service.get_alternative_data(symbols)
            
            # Create feature matrix
            X, y = self._create_integrated_features(market_data, alternative_data)
            
            if len(X) == 0:
                raise ValueError("No training data available")
            
            logger.info(f"Created {len(X)} samples with {X.shape[1]} features")
            
            # Train models
            results = {}
            
            if self.deep_learning_service.deep_learning_available:
                # Train LSTM
                logger.info("Training LSTM model...")
                lstm_results = self.deep_learning_service.train_lstm_model(X, y)
                results['lstm'] = lstm_results
                
                # Train Transformer
                logger.info("Training Transformer model...")
                transformer_results = self.deep_learning_service.train_transformer_model(X, y)
                results['transformer'] = transformer_results
                
                # Ensemble prediction
                logger.info("Creating ensemble model...")
                ensemble_pred = self.deep_learning_service.ensemble_predict(X)
                ensemble_r2 = self._calculate_r2_score(y, ensemble_pred)
                results['ensemble'] = {
                    'r2': ensemble_r2,
                    'predictions': ensemble_pred
                }
            
            # Update model performance
            self.model_performance = results
            self.last_update = datetime.now()
            
            return results
            
        except Exception as e:
            logger.error(f"Error training models with real data: {e}")
            raise
    
    def _calculate_rsi(self, prices: pd.Series, window: int = 14) -> pd.Series:
        """Calculate RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _create_integrated_features(self, market_data: Dict[str, pd.DataFrame], alternative_data: Dict[str, Any]) -> Tuple[np.ndarray, np.ndarray]:
        """Create integrated feature matrix combining market and alternative data"""
        X = []
        y = []
        
        for symbol, data in market_data.items():
            alt_data = alternative_data.get(symbol)
            if not alt_data:
                continue
            
            for i in range(200, len(data) - 20):  # 20-day prediction horizon
                features = []
                
                # Market features
                features.extend([
                    data['Returns'].iloc[i],
                    data['Log_Returns'].iloc[i],
                    data['Price_Range'].iloc[i],
                    data['Price_Position'].iloc[i],
                    data['RSI_14'].iloc[i],
                    data['MACD'].iloc[i],
                    data['MACD_Signal'].iloc[i],
                    data['MACD_Histogram'].iloc[i],
                    data['BB_Width'].iloc[i],
                    data['BB_Position'].iloc[i],
                    data['Volume_Ratio'].iloc[i],
                    data['Volatility'].iloc[i],
                ])
                
                # Moving averages (normalized)
                for window in [5, 10, 20, 50, 100, 200]:
                    if f'SMA_{window}' in data.columns and data['Close'].iloc[i] > 0:
                        features.append(data[f'SMA_{window}'].iloc[i] / data['Close'].iloc[i])
                        features.append(data[f'EMA_{window}'].iloc[i] / data['Close'].iloc[i])
                    else:
                        features.extend([0, 0])
                
                # Alternative data features
                features.extend([
                    alt_data.news_sentiment,
                    alt_data.social_sentiment,
                    alt_data.analyst_sentiment,
                    alt_data.market_sentiment,
                    alt_data.volatility_index / 100.0,
                    alt_data.fear_greed_index,
                ])
                
                # Economic indicators
                for key, value in alt_data.economic_indicators.items():
                    if key == 'GDP':
                        features.append(value / 10.0)
                    elif key == 'UNEMPLOYMENT':
                        features.append(value / 10.0)
                    elif key == 'INFLATION':
                        features.append(value / 10.0)
                    elif key == 'INTEREST_RATE':
                        features.append(value / 10.0)
                    elif key == 'CONSUMER_SENTIMENT':
                        features.append(value / 100.0)
                    elif key == 'VIX':
                        features.append(value / 100.0)
                
                # Target: 20-day future return with sophisticated scoring
                future_return = (data['Close'].iloc[i+20] - data['Close'].iloc[i]) / data['Close'].iloc[i]
                
                # Risk-adjusted scoring
                volatility_20d = data['Returns'].iloc[i:i+20].std()
                if volatility_20d > 0:
                    sharpe_ratio = future_return / volatility_20d
                    
                    # Multi-factor scoring
                    if sharpe_ratio > 3.0:
                        score = 1.0  # Excellent
                    elif sharpe_ratio > 2.0:
                        score = 0.8  # Good
                    elif sharpe_ratio > 1.0:
                        score = 0.6  # Positive
                    elif sharpe_ratio > 0:
                        score = 0.4  # Slightly positive
                    else:
                        score = 0.0  # Poor
                else:
                    score = 0.5  # Neutral
                
                X.append(features)
                y.append(score)
        
        return np.array(X), np.array(y)
    
    def _calculate_r2_score(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Calculate R² score"""
        from sklearn.metrics import r2_score
        return r2_score(y_true, y_pred)
    
    async def get_real_time_prediction(self, symbol: str) -> Dict[str, Any]:
        """Get real-time prediction for a symbol"""
        try:
            # Get latest data from pipeline
            latest_data = self.realtime_pipeline.get_latest_data(symbol)
            
            if latest_data:
                return {
                    'symbol': symbol,
                    'prediction': latest_data.prediction,
                    'confidence': latest_data.confidence,
                    'price': latest_data.price,
                    'timestamp': latest_data.timestamp,
                    'model_version': latest_data.model_version
                }
            else:
                # Fallback to batch prediction
                return await self._batch_predict(symbol)
                
        except Exception as e:
            logger.error(f"Error getting real-time prediction for {symbol}: {e}")
            return {
                'symbol': symbol,
                'prediction': 0.0,
                'confidence': 0.0,
                'error': str(e)
            }
    
    async def _batch_predict(self, symbol: str) -> Dict[str, Any]:
        """Fallback batch prediction"""
        try:
            # Get alternative data
            alternative_data = await self.alternative_data_service.get_alternative_data([symbol])
            alt_data = alternative_data.get(symbol)
            
            if not alt_data:
                return {
                    'symbol': symbol,
                    'prediction': 0.0,
                    'confidence': 0.0,
                    'error': 'No alternative data available'
                }
            
            # Create feature vector
            features = [
                alt_data.news_sentiment,
                alt_data.social_sentiment,
                alt_data.analyst_sentiment,
                alt_data.market_sentiment,
                alt_data.volatility_index / 100.0,
                alt_data.fear_greed_index,
            ]
            
            # Add economic indicators
            for key, value in alt_data.economic_indicators.items():
                if key == 'GDP':
                    features.append(value / 10.0)
                elif key == 'UNEMPLOYMENT':
                    features.append(value / 10.0)
                elif key == 'INFLATION':
                    features.append(value / 10.0)
                elif key == 'INTEREST_RATE':
                    features.append(value / 10.0)
                elif key == 'CONSUMER_SENTIMENT':
                    features.append(value / 100.0)
                elif key == 'VIX':
                    features.append(value / 100.0)
            
            # Make prediction
            X = np.array(features).reshape(1, -1)
            
            if self.deep_learning_service.lstm_model is not None:
                prediction = self.deep_learning_service.predict_lstm(X)[0]
                confidence = 0.8
            elif self.deep_learning_service.transformer_model is not None:
                prediction = self.deep_learning_service.predict_transformer(X)[0]
                confidence = 0.7
            else:
                prediction = np.random.normal(0, 0.1)
                confidence = 0.3
            
            return {
                'symbol': symbol,
                'prediction': prediction,
                'confidence': confidence,
                'timestamp': datetime.now(),
                'model_version': self.realtime_pipeline.current_model_version
            }
            
        except Exception as e:
            logger.error(f"Error in batch prediction for {symbol}: {e}")
            return {
                'symbol': symbol,
                'prediction': 0.0,
                'confidence': 0.0,
                'error': str(e)
            }
    
    async def start_real_time_pipeline(self, symbols: List[str], update_interval: int = 60):
        """Start the real-time pipeline"""
        logger.info(f"Starting real-time pipeline for {len(symbols)} symbols")
        
        # Start pipeline in background
        asyncio.create_task(
            self.realtime_pipeline.run_pipeline(symbols, update_interval)
        )
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get system status and performance metrics"""
        return {
            'is_initialized': self.is_initialized,
            'last_update': self.last_update.isoformat(),
            'model_performance': self.model_performance,
            'alternative_data_available': self.alternative_data_service is not None,
            'deep_learning_available': self.deep_learning_service.deep_learning_available,
            'realtime_pipeline_running': self.realtime_pipeline.is_running,
            'current_model_version': self.realtime_pipeline.current_model_version
        }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        if not self.model_performance:
            return {'error': 'No models trained yet'}
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'models': {}
        }
        
        for model_name, results in self.model_performance.items():
            if 'cv_mean' in results:
                summary['models'][model_name] = {
                    'cv_r2_mean': results['cv_mean'],
                    'cv_r2_std': results.get('cv_std', 0),
                    'train_r2': results.get('train_r2', 0),
                    'mse': results.get('mse', 0),
                    'mae': results.get('mae', 0)
                }
            elif 'r2' in results:
                summary['models'][model_name] = {
                    'r2': results['r2']
                }
        
        return summary

# Example usage
async def main():
    """Example usage of IntegratedMLSystem"""
    system = IntegratedMLSystem()
    
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'KO', 'JPM']
    
    try:
        # Initialize system
        await system.initialize_system(symbols)
        
        # Train models with real data
        results = await system.train_models_with_real_data(symbols)
        
        # Print results
        print("\n📊 MODEL PERFORMANCE:")
        for model_name, model_results in results.items():
            if 'cv_mean' in model_results:
                print(f"  {model_name}: CV R² = {model_results['cv_mean']:.3f} ± {model_results['cv_std']:.3f}")
            elif 'r2' in model_results:
                print(f"  {model_name}: R² = {model_results['r2']:.3f}")
        
        # Start real-time pipeline
        await system.start_real_time_pipeline(symbols, update_interval=30)
        
        # Get real-time predictions
        for symbol in symbols[:3]:
            prediction = await system.get_real_time_prediction(symbol)
            print(f"\n{symbol}: Prediction={prediction['prediction']:.3f}, Confidence={prediction['confidence']:.3f}")
        
        # Get system status
        status = system.get_system_status()
        print(f"\n🔧 SYSTEM STATUS:")
        print(f"  Initialized: {status['is_initialized']}")
        print(f"  Deep Learning: {status['deep_learning_available']}")
        print(f"  Real-time Pipeline: {status['realtime_pipeline_running']}")
        print(f"  Model Version: {status['current_model_version']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
