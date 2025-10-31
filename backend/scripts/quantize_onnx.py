#!/usr/bin/env python3
"""
ONNX Model Quantization Script
===============================
Quantizes ONNX models to INT8 for faster inference.

Usage:
    python scripts/quantize_onnx.py model.onnx model.int8.onnx
"""

import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from onnxruntime.quantization import quantize_dynamic, QuantType
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False
    logger.error("onnxruntime not installed. Install with: pip install onnxruntime")
    sys.exit(1)


def quantize_model(input_path: str, output_path: str):
    """
    Quantize ONNX model to INT8.
    
    Args:
        input_path: Path to input .onnx model
        output_path: Path to save quantized model
    """
    input_file = Path(input_path)
    output_file = Path(output_path)
    
    if not input_file.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    logger.info(f"Quantizing {input_path} -> {output_path}")
    
    try:
        quantize_dynamic(
            str(input_file),
            str(output_file),
            weight_type=QuantType.QInt8
        )
        logger.info(f"✅ Quantization complete: {output_path}")
    except Exception as e:
        logger.error(f"Quantization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python quantize_onnx.py <input.onnx> <output.int8.onnx>")
        sys.exit(1)
    
    quantize_model(sys.argv[1], sys.argv[2])

