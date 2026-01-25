# ML Models Directory

Place your TensorFlow Lite models here.

## Required Model

- **strategy_predictor.tflite** - Trading strategy prediction model

## Model Training

To create this model:

1. Run the training script:
   ```bash
   cd ../../scripts
   python3 train_strategy_model_example.py
   ```

2. Copy the generated model:
   ```bash
   cp strategy_predictor.tflite ../assets/models/
   ```

## Model Specifications

- **Input Shape**: `[1, 10]` (10 features)
- **Output Shape**: `[1, 1]` (success probability 0-1)
- **Format**: TensorFlow Lite (quantized)
- **Expected Size**: 500KB-1MB

## Features (in order)

1. Volatility (0-1)
2. Volume (0-1)
3. Momentum (-1 to 1)
4. Regime (0-1)
5. Spread (normalized)
6. ATR (0-1)
7. RSI (0-1)
8. MACD (-1 to 1)
9. Trend (0-1)
10. Time of Day (0-1)

See `mlFeatureExtraction.ts` for feature extraction logic.

