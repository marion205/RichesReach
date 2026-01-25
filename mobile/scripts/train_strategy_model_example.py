#!/usr/bin/env python3
"""
Example script for training a trading strategy prediction model
and converting it to TensorFlow Lite format for mobile deployment.

Usage:
    python train_strategy_model_example.py

Output:
    strategy_predictor.tflite - Quantized model ready for mobile
"""

import tensorflow as tf
import numpy as np
from pathlib import Path

# Set random seeds for reproducibility
np.random.seed(42)
tf.random.set_seed(42)

def generate_synthetic_data(n_samples=10000):
    """
    Generate synthetic training data.
    In production, replace this with your real trading data.
    """
    X = np.random.randn(n_samples, 10).astype(np.float32)
    
    # Create synthetic labels based on feature combinations
    # Higher volatility + positive momentum + bullish regime = higher success
    success_prob = (
        (X[:, 0] > 0) * 0.3 +  # Volatility
        (X[:, 2] > 0) * 0.3 +  # Momentum
        (X[:, 3] > 0.5) * 0.3 +  # Regime
        np.random.rand(n_samples) * 0.1  # Noise
    )
    y = (success_prob > 0.5).astype(np.float32)
    
    return X, y

def create_model():
    """Create the neural network model architecture."""
    model = tf.keras.Sequential([
        tf.keras.layers.Dense(64, activation='relu', input_shape=(10,)),
        tf.keras.layers.Dropout(0.2),
        tf.keras.layers.Dense(32, activation='relu'),
        tf.keras.layers.Dropout(0.2),
        tf.keras.layers.Dense(1, activation='sigmoid')  # Success probability
    ])
    
    model.compile(
        optimizer='adam',
        loss='binary_crossentropy',
        metrics=['accuracy', 'precision', 'recall']
    )
    
    return model

def train_model(model, X_train, y_train, X_val, y_val):
    """Train the model with early stopping."""
    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor='val_loss',
            patience=10,
            restore_best_weights=True
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=5,
            min_lr=1e-6
        )
    ]
    
    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=100,
        batch_size=32,
        callbacks=callbacks,
        verbose=1
    )
    
    return history

def convert_to_tflite(model, quantization='float16'):
    """
    Convert Keras model to TensorFlow Lite with quantization.
    
    Args:
        model: Trained Keras model
        quantization: 'float16', 'int8', or 'none'
    """
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    
    if quantization == 'float16':
        # Float16 quantization (good balance of size and accuracy)
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        converter.target_spec.supported_types = [tf.float16]
        print("Using float16 quantization")
        
    elif quantization == 'int8':
        # INT8 quantization (smallest, fastest, but may lose accuracy)
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        
        def representative_dataset():
            # Use a subset of training data for calibration
            for i in range(100):
                yield [X_train[i:i+1].astype(np.float32)]
        
        converter.representative_dataset = representative_dataset
        converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
        converter.inference_input_type = tf.int8
        converter.inference_output_type = tf.int8
        print("Using INT8 quantization")
        
    else:
        # No quantization (largest, most accurate)
        print("No quantization")
    
    tflite_model = converter.convert()
    return tflite_model

def main():
    print("=" * 60)
    print("Trading Strategy Model Training & Conversion")
    print("=" * 60)
    
    # Generate or load your training data
    print("\n1. Loading training data...")
    X, y = generate_synthetic_data(n_samples=10000)
    
    # Split into train/validation
    split_idx = int(len(X) * 0.8)
    X_train, X_val = X[:split_idx], X[split_idx:]
    y_train, y_val = y[:split_idx], y[split_idx:]
    
    print(f"   Training samples: {len(X_train)}")
    print(f"   Validation samples: {len(X_val)}")
    
    # Create model
    print("\n2. Creating model architecture...")
    model = create_model()
    model.summary()
    
    # Train model
    print("\n3. Training model...")
    history = train_model(model, X_train, y_train, X_val, y_val)
    
    # Evaluate
    print("\n4. Evaluating model...")
    val_loss, val_accuracy, val_precision, val_recall = model.evaluate(X_val, y_val, verbose=0)
    print(f"   Validation Accuracy: {val_accuracy:.4f}")
    print(f"   Validation Precision: {val_precision:.4f}")
    print(f"   Validation Recall: {val_recall:.4f}")
    
    # Convert to TFLite
    print("\n5. Converting to TensorFlow Lite...")
    
    # Try float16 first (recommended)
    try:
        tflite_model = convert_to_tflite(model, quantization='float16')
        output_path = Path('strategy_predictor.tflite')
        output_path.write_bytes(tflite_model)
        
        size_kb = len(tflite_model) / 1024
        print(f"   ✅ Model saved: {output_path}")
        print(f"   Model size: {size_kb:.2f} KB")
        
    except Exception as e:
        print(f"   ⚠️  Float16 conversion failed: {e}")
        print("   Trying without quantization...")
        
        tflite_model = convert_to_tflite(model, quantization='none')
        output_path = Path('strategy_predictor.tflite')
        output_path.write_bytes(tflite_model)
        
        size_kb = len(tflite_model) / 1024
        print(f"   ✅ Model saved: {output_path}")
        print(f"   Model size: {size_kb:.2f} KB")
    
    # Test inference
    print("\n6. Testing TFLite inference...")
    interpreter = tf.lite.Interpreter(model_content=tflite_model)
    interpreter.allocate_tensors()
    
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    
    # Test with a sample
    test_input = X_val[0:1].astype(np.float32)
    interpreter.set_tensor(input_details[0]['index'], test_input)
    interpreter.invoke()
    
    output = interpreter.get_tensor(output_details[0]['index'])
    print(f"   Test input shape: {test_input.shape}")
    print(f"   Test output: {output[0][0]:.4f}")
    print(f"   Expected: {y_val[0]:.0f}")
    
    print("\n" + "=" * 60)
    print("✅ Model training and conversion complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Copy strategy_predictor.tflite to your mobile app")
    print("2. iOS: Add to Xcode project")
    print("3. Android: Copy to android/app/src/main/assets/")
    print("4. Test inference in the app")

if __name__ == '__main__':
    main()

