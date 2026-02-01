"""
Model Optimization Utilities
Convert models to ONNX/TensorRT for faster inference.
"""
import logging
import os
from typing import Optional, Dict, Any
import numpy as np

logger = logging.getLogger(__name__)


class ModelOptimizer:
    """
    Convert models to optimized formats (ONNX, TensorRT) for faster inference.
    """
    
    def __init__(self):
        self.models_dir = os.path.join(os.path.dirname(__file__), 'models')
        os.makedirs(self.models_dir, exist_ok=True)
    
    def convert_lstm_to_onnx(
        self,
        model_path: str,
        output_path: Optional[str] = None,
        input_shape: tuple = (1, 60, 5)  # (batch, timesteps, features)
    ) -> bool:
        """
        Convert LSTM model to ONNX format.
        
        Args:
            model_path: Path to Keras/TensorFlow model
            output_path: Output ONNX path (default: models/lstm_extractor.onnx)
            input_shape: Input shape for ONNX conversion
        
        Returns:
            True if conversion successful
        """
        try:
            import onnx
            from onnxruntime import InferenceSession
            import tensorflow as tf
            from tf2onnx import convert
            
            if output_path is None:
                output_path = os.path.join(self.models_dir, 'lstm_extractor.onnx')
            
            logger.info(f"Converting LSTM model to ONNX: {model_path} -> {output_path}")
            
            # Load Keras model with custom objects to handle version compatibility
            try:
                keras_model = tf.keras.models.load_model(model_path)
            except Exception as e:
                # Try loading with compile=False to avoid metric deserialization issues
                logger.warning(f"Standard load failed, trying with compile=False: {e}")
                keras_model = tf.keras.models.load_model(model_path, compile=False)
                # Recompile if needed
                if hasattr(keras_model, 'compile'):
                    keras_model.compile(optimizer='adam', loss='mse')
            
            # Convert to ONNX
            onnx_model, _ = convert.from_keras(
                keras_model,
                input_signature=[tf.TensorSpec(shape=input_shape, dtype=tf.float32, name='input')],
                output_path=output_path
            )
            
            # Verify ONNX model
            session = InferenceSession(output_path)
            logger.info(f"✅ LSTM model converted to ONNX: {output_path}")
            logger.info(f"   Input shape: {session.get_inputs()[0].shape}")
            logger.info(f"   Output shape: {session.get_outputs()[0].shape}")
            
            return True
            
        except ImportError:
            logger.warning("⚠️ ONNX dependencies not installed. Install with: pip install onnx onnxruntime tf2onnx")
            return False
        except Exception as e:
            logger.error(f"❌ Error converting LSTM to ONNX: {e}", exc_info=True)
            return False
    
    def convert_xgboost_to_onnx(
        self,
        model_path: str,
        output_path: Optional[str] = None,
        n_features: int = 20
    ) -> bool:
        """
        Convert XGBoost model to ONNX format.
        
        Args:
            model_path: Path to XGBoost model (.pkl or .json)
            output_path: Output ONNX path (default: models/xgboost_model.onnx)
            n_features: Number of input features
        
        Returns:
            True if conversion successful
        """
        try:
            import onnx
            from onnxruntime import InferenceSession
            import xgboost as xgb
            from onnxmltools import convert_xgboost
            
            if output_path is None:
                output_path = os.path.join(self.models_dir, 'xgboost_model.onnx')
            
            logger.info(f"Converting XGBoost model to ONNX: {model_path} -> {output_path}")
            
            # Load XGBoost model
            if model_path.endswith('.json'):
                xgb_model = xgb.XGBClassifier()
                xgb_model.load_model(model_path)
            else:
                import joblib
                xgb_model = joblib.load(model_path)
            
            # Convert to ONNX using onnxmltools (not skl2onnx)
            from onnxmltools.convert.common.data_types import FloatTensorType
            initial_type = [('input', FloatTensorType([None, n_features]))]
            onnx_model = convert_xgboost(xgb_model, initial_types=initial_type)
            
            # Save ONNX model
            with open(output_path, 'wb') as f:
                f.write(onnx_model.SerializeToString())
            
            # Verify ONNX model
            session = InferenceSession(output_path)
            logger.info(f"✅ XGBoost model converted to ONNX: {output_path}")
            logger.info(f"   Input shape: {session.get_inputs()[0].shape}")
            logger.info(f"   Output shape: {session.get_outputs()[0].shape}")
            
            return True
            
        except ImportError:
            logger.warning("⚠️ ONNX dependencies not installed. Install with: pip install onnx onnxruntime onnxmltools")
            return False
        except Exception as e:
            logger.error(f"❌ Error converting XGBoost to ONNX: {e}", exc_info=True)
            return False
    
    def load_onnx_model(self, model_path: str):
        """
        Load ONNX model for inference.
        
        Args:
            model_path: Path to ONNX model
        
        Returns:
            ONNX InferenceSession or None
        """
        try:
            from onnxruntime import InferenceSession
            
            if not os.path.exists(model_path):
                logger.warning(f"ONNX model not found: {model_path}")
                return None
            
            session = InferenceSession(model_path)
            logger.info(f"✅ Loaded ONNX model: {model_path}")
            return session
            
        except ImportError:
            logger.warning("⚠️ ONNXRuntime not installed")
            return None
        except Exception as e:
            logger.error(f"❌ Error loading ONNX model: {e}")
            return None
    
    def predict_with_onnx(
        self,
        session,
        input_data: np.ndarray,
        input_name: str = 'input'
    ) -> np.ndarray:
        """
        Run inference with ONNX model.
        
        Args:
            session: ONNX InferenceSession
            input_data: Input data array
            input_name: Input tensor name
        
        Returns:
            Prediction array
        """
        try:
            # Get input name from model if not provided
            if input_name is None:
                input_name = session.get_inputs()[0].name
            
            # Run inference
            outputs = session.run(None, {input_name: input_data})
            return outputs[0]
            
        except Exception as e:
            logger.error(f"❌ Error running ONNX inference: {e}")
            raise


# Global instance
_model_optimizer = None

def get_model_optimizer() -> ModelOptimizer:
    """Get global model optimizer instance"""
    global _model_optimizer
    if _model_optimizer is None:
        _model_optimizer = ModelOptimizer()
    return _model_optimizer

