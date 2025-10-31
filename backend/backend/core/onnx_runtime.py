"""
ONNX Runtime Integration
========================
High-performance ML inference using ONNX Runtime with optimization.

Usage:
    from core.onnx_runtime import get_onnx_session, quantize_model
    
    session = get_onnx_session("models/regime_predictor.onnx")
    outputs = session.run(None, {"input": input_array})
"""

from __future__ import annotations

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

# ONNX Runtime imports (optional)
try:
    from onnxruntime import (
        InferenceSession,
        SessionOptions,
        GraphOptimizationLevel,
        ExecutionMode,
    )
    from onnxruntime.quantization import quantize_dynamic, QuantType
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False
    logger.warning("onnxruntime not installed. ONNX inference disabled.")


class ONNXModelManager:
    """Manages ONNX model sessions with optimized settings."""
    
    def __init__(self, num_threads: int = 2):
        self.num_threads = num_threads
        self._sessions: Dict[str, InferenceSession] = {}
    
    def get_session(self, model_path: str, use_quantized: bool = True) -> InferenceSession:
        """
        Get or create an ONNX session for a model.
        
        Args:
            model_path: Path to .onnx model file
            use_quantized: Prefer quantized version if available
            
        Returns:
            InferenceSession with optimized settings
        """
        if not ONNX_AVAILABLE:
            raise RuntimeError("ONNX Runtime not available")
        
        # Check for quantized version
        if use_quantized:
            quantized_path = str(model_path).replace('.onnx', '.int8.onnx')
            if Path(quantized_path).exists():
                model_path = quantized_path
                logger.info(f"Using quantized model: {quantized_path}")
        
        model_path = str(Path(model_path))
        
        # Return cached session if available
        if model_path in self._sessions:
            return self._sessions[model_path]
        
        # Create optimized session
        so = SessionOptions()
        so.graph_optimization_level = GraphOptimizationLevel.ORT_ENABLE_ALL
        so.intra_op_num_threads = self.num_threads
        so.inter_op_num_threads = 1
        so.enable_mem_pattern = True
        so.execution_mode = ExecutionMode.ORT_SEQUENTIAL
        
        # Provider priority: CPU (CUDA can be added if available)
        providers = ["CPUExecutionProvider"]
        
        try:
            session = InferenceSession(
                model_path,
                sess_options=so,
                providers=providers
            )
            self._sessions[model_path] = session
            logger.info(f"Created ONNX session for {model_path}")
            return session
        except Exception as e:
            logger.error(f"Failed to create ONNX session: {e}")
            raise
    
    def run_inference(
        self,
        model_path: str,
        inputs: Dict[str, Any],
        output_names: Optional[List[str]] = None
    ) -> List[Any]:
        """
        Run inference on a model.
        
        Args:
            model_path: Path to ONNX model
            inputs: Input dictionary (tensor name -> numpy array)
            output_names: Optional list of output names to fetch
            
        Returns:
            List of output tensors
        """
        session = self.get_session(model_path)
        outputs = session.run(output_names, inputs)
        return outputs


# Global manager instance
_onnx_manager = ONNXModelManager()


def get_onnx_session(model_path: str, use_quantized: bool = True) -> InferenceSession:
    """Get an optimized ONNX session."""
    return _onnx_manager.get_session(model_path, use_quantized)


def run_onnx_inference(
    model_path: str,
    inputs: Dict[str, Any],
    output_names: Optional[List[str]] = None
) -> List[Any]:
    """Run inference using ONNX Runtime."""
    return _onnx_manager.run_inference(model_path, inputs, output_names)


def quantize_model(input_path: str, output_path: str) -> None:
    """
    Quantize an ONNX model to INT8 for faster inference.
    
    Args:
        input_path: Path to original .onnx model
        output_path: Path to save quantized .int8.onnx model
    """
    if not ONNX_AVAILABLE:
        raise RuntimeError("ONNX Runtime not available")
    
    logger.info(f"Quantizing {input_path} -> {output_path}")
    quantize_dynamic(
        input_path,
        output_path,
        weight_type=QuantType.QInt8
    )
    logger.info(f"Quantization complete: {output_path}")

