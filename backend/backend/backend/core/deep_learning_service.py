"""
Deep Learning Service
Implements LSTM and Transformer models for stock prediction
"""
import os
import sys
import django
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')
# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()
# Deep Learning imports
try:
import tensorflow as tf
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import LSTM, Dense, Dropout, Input, MultiHeadAttention, LayerNormalization, GlobalAveragePooling1D
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.regularizers import l1_l2
from sklearn.preprocessing import MinMaxScaler, RobustScaler
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
DEEP_LEARNING_AVAILABLE = True
except ImportError as e:
logging.warning(f"Deep learning libraries not available: {e}")
DEEP_LEARNING_AVAILABLE = False
logger = logging.getLogger(__name__)
class DeepLearningService:
"""
Deep learning service for stock prediction using LSTM and Transformer models
"""
def __init__(self):
self.deep_learning_available = DEEP_LEARNING_AVAILABLE
if not self.deep_learning_available:
logger.warning("Deep Learning Service initialized in fallback mode")
# Model parameters
self.sequence_length = 60 # 60 days of historical data
self.prediction_horizon = 20 # 20 days ahead
self.feature_dim = 50 # Number of features
# Models
self.lstm_model = None
self.transformer_model = None
self.scaler = RobustScaler()
# Training parameters
self.lstm_params = {
'lstm_units': [128, 64, 32],
'dropout_rate': 0.2,
'recurrent_dropout': 0.2,
'dense_units': [64, 32],
'learning_rate': 0.001,
'batch_size': 32,
'epochs': 100,
'patience': 15
}
self.transformer_params = {
'd_model': 128,
'num_heads': 8,
'num_layers': 4,
'dff': 512,
'dropout_rate': 0.1,
'learning_rate': 0.001,
'batch_size': 32,
'epochs': 100,
'patience': 15
}
def create_lstm_model(self, input_shape: Tuple[int, int]) -> Model:
"""Create LSTM model for time series prediction"""
model = Sequential()
# First LSTM layer
model.add(LSTM(
units=self.lstm_params['lstm_units'][0],
return_sequences=True,
input_shape=input_shape,
dropout=self.lstm_params['dropout_rate'],
recurrent_dropout=self.lstm_params['recurrent_dropout'],
kernel_regularizer=l1_l2(l1=0.01, l2=0.01)
))
# Additional LSTM layers
for units in self.lstm_params['lstm_units'][1:]:
model.add(LSTM(
units=units,
return_sequences=True,
dropout=self.lstm_params['dropout_rate'],
recurrent_dropout=self.lstm_params['recurrent_dropout'],
kernel_regularizer=l1_l2(l1=0.01, l2=0.01)
))
# Final LSTM layer (no return sequences)
model.add(LSTM(
units=self.lstm_params['lstm_units'][-1],
return_sequences=False,
dropout=self.lstm_params['dropout_rate'],
recurrent_dropout=self.lstm_params['recurrent_dropout'],
kernel_regularizer=l1_l2(l1=0.01, l2=0.01)
))
# Dense layers
for units in self.lstm_params['dense_units']:
model.add(Dense(
units=units,
activation='relu',
kernel_regularizer=l1_l2(l1=0.01, l2=0.01)
))
model.add(Dropout(self.lstm_params['dropout_rate']))
# Output layer
model.add(Dense(1, activation='linear'))
# Compile model
model.compile(
optimizer=Adam(learning_rate=self.lstm_params['learning_rate']),
loss='mse',
metrics=['mae', 'mape']
)
return model
def create_transformer_model(self, input_shape: Tuple[int, int]) -> Model:
"""Create Transformer model for time series prediction"""
inputs = Input(shape=input_shape)
# Input projection
x = Dense(self.transformer_params['d_model'])(inputs)
# Transformer layers
for _ in range(self.transformer_params['num_layers']):
# Multi-head attention
attn_output = MultiHeadAttention(
num_heads=self.transformer_params['num_heads'],
key_dim=self.transformer_params['d_model'] // self.transformer_params['num_heads'],
dropout=self.transformer_params['dropout_rate']
)(x, x)
# Add & Norm
x = LayerNormalization(epsilon=1e-6)(x + attn_output)
# Feed forward
ffn = Dense(self.transformer_params['dff'], activation='relu')(x)
ffn = Dropout(self.transformer_params['dropout_rate'])(ffn)
ffn = Dense(self.transformer_params['d_model'])(ffn)
# Add & Norm
x = LayerNormalization(epsilon=1e-6)(x + ffn)
# Global average pooling
x = GlobalAveragePooling1D()(x)
# Dense layers
x = Dense(128, activation='relu')(x)
x = Dropout(self.transformer_params['dropout_rate'])(x)
x = Dense(64, activation='relu')(x)
x = Dropout(self.transformer_params['dropout_rate'])(x)
# Output layer
outputs = Dense(1, activation='linear')(x)
model = Model(inputs=inputs, outputs=outputs)
# Compile model
model.compile(
optimizer=Adam(learning_rate=self.transformer_params['learning_rate']),
loss='mse',
metrics=['mae', 'mape']
)
return model
def prepare_sequences(self, data: np.ndarray, target: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
"""Prepare sequences for LSTM/Transformer training"""
X, y = [], []
for i in range(self.sequence_length, len(data) - self.prediction_horizon + 1):
# Input sequence
X.append(data[i-self.sequence_length:i])
# Target (future value)
y.append(target[i + self.prediction_horizon - 1])
return np.array(X), np.array(y)
def train_lstm_model(self, X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
"""Train LSTM model"""
logger.info("Training LSTM model...")
# Prepare sequences
X_seq, y_seq = self.prepare_sequences(X, y)
# Scale features
X_scaled = self.scaler.fit_transform(X_seq.reshape(-1, X_seq.shape[-1])).reshape(X_seq.shape)
# Time series split for validation
tscv = TimeSeriesSplit(n_splits=5)
# Create model
input_shape = (X_scaled.shape[1], X_scaled.shape[2])
self.lstm_model = self.create_lstm_model(input_shape)
# Callbacks
callbacks = [
EarlyStopping(
monitor='val_loss',
patience=self.lstm_params['patience'],
restore_best_weights=True
),
ReduceLROnPlateau(
monitor='val_loss',
factor=0.5,
patience=10,
min_lr=1e-7
)
]
# Cross-validation
cv_scores = []
for train_idx, val_idx in tscv.split(X_scaled):
X_train, X_val = X_scaled[train_idx], X_scaled[val_idx]
y_train, y_val = y_seq[train_idx], y_seq[val_idx]
# Train model
history = self.lstm_model.fit(
X_train, y_train,
validation_data=(X_val, y_val),
epochs=self.lstm_params['epochs'],
batch_size=self.lstm_params['batch_size'],
callbacks=callbacks,
verbose=0
)
# Evaluate
val_pred = self.lstm_model.predict(X_val, verbose=0)
val_r2 = r2_score(y_val, val_pred)
cv_scores.append(val_r2)
# Train on full data
self.lstm_model.fit(
X_scaled, y_seq,
epochs=self.lstm_params['epochs'],
batch_size=self.lstm_params['batch_size'],
callbacks=callbacks,
verbose=0
)
# Final evaluation
train_pred = self.lstm_model.predict(X_scaled, verbose=0)
train_r2 = r2_score(y_seq, train_pred)
train_mse = mean_squared_error(y_seq, train_pred)
train_mae = mean_absolute_error(y_seq, train_pred)
return {
'model': self.lstm_model,
'cv_mean': np.mean(cv_scores),
'cv_std': np.std(cv_scores),
'cv_scores': cv_scores,
'train_r2': train_r2,
'train_mse': train_mse,
'train_mae': train_mae,
'predictions': train_pred
}
def train_transformer_model(self, X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
"""Train Transformer model"""
logger.info("Training Transformer model...")
# Prepare sequences
X_seq, y_seq = self.prepare_sequences(X, y)
# Scale features
X_scaled = self.scaler.fit_transform(X_seq.reshape(-1, X_seq.shape[-1])).reshape(X_seq.shape)
# Time series split for validation
tscv = TimeSeriesSplit(n_splits=5)
# Create model
input_shape = (X_scaled.shape[1], X_scaled.shape[2])
self.transformer_model = self.create_transformer_model(input_shape)
# Callbacks
callbacks = [
EarlyStopping(
monitor='val_loss',
patience=self.transformer_params['patience'],
restore_best_weights=True
),
ReduceLROnPlateau(
monitor='val_loss',
factor=0.5,
patience=10,
min_lr=1e-7
)
]
# Cross-validation
cv_scores = []
for train_idx, val_idx in tscv.split(X_scaled):
X_train, X_val = X_scaled[train_idx], X_scaled[val_idx]
y_train, y_val = y_seq[train_idx], y_seq[val_idx]
# Train model
history = self.transformer_model.fit(
X_train, y_train,
validation_data=(X_val, y_val),
epochs=self.transformer_params['epochs'],
batch_size=self.transformer_params['batch_size'],
callbacks=callbacks,
verbose=0
)
# Evaluate
val_pred = self.transformer_model.predict(X_val, verbose=0)
val_r2 = r2_score(y_val, val_pred)
cv_scores.append(val_r2)
# Train on full data
self.transformer_model.fit(
X_scaled, y_seq,
epochs=self.transformer_params['epochs'],
batch_size=self.transformer_params['batch_size'],
callbacks=callbacks,
verbose=0
)
# Final evaluation
train_pred = self.transformer_model.predict(X_scaled, verbose=0)
train_r2 = r2_score(y_seq, train_pred)
train_mse = mean_squared_error(y_seq, train_pred)
train_mae = mean_absolute_error(y_seq, train_pred)
return {
'model': self.transformer_model,
'cv_mean': np.mean(cv_scores),
'cv_std': np.std(cv_scores),
'cv_scores': cv_scores,
'train_r2': train_r2,
'train_mse': train_mse,
'train_mae': train_mae,
'predictions': train_pred
}
def predict_lstm(self, X: np.ndarray) -> np.ndarray:
"""Make predictions using LSTM model"""
if self.lstm_model is None:
raise ValueError("LSTM model not trained yet")
# Prepare sequences
X_seq, _ = self.prepare_sequences(X, np.zeros(len(X)))
# Scale features
X_scaled = self.scaler.transform(X_seq.reshape(-1, X_seq.shape[-1])).reshape(X_seq.shape)
# Make predictions
predictions = self.lstm_model.predict(X_scaled, verbose=0)
return predictions.flatten()
def predict_transformer(self, X: np.ndarray) -> np.ndarray:
"""Make predictions using Transformer model"""
if self.transformer_model is None:
raise ValueError("Transformer model not trained yet")
# Prepare sequences
X_seq, _ = self.prepare_sequences(X, np.zeros(len(X)))
# Scale features
X_scaled = self.scaler.transform(X_seq.reshape(-1, X_seq.shape[-1])).reshape(X_seq.shape)
# Make predictions
predictions = self.transformer_model.predict(X_scaled, verbose=0)
return predictions.flatten()
def ensemble_predict(self, X: np.ndarray) -> np.ndarray:
"""Make ensemble predictions using both models"""
if self.lstm_model is None or self.transformer_model is None:
raise ValueError("Both models must be trained for ensemble prediction")
lstm_pred = self.predict_lstm(X)
transformer_pred = self.predict_transformer(X)
# Weighted ensemble (can be optimized)
ensemble_pred = 0.6 * lstm_pred + 0.4 * transformer_pred
return ensemble_pred