import { useState, useEffect, useRef } from 'react';
import { Platform } from 'react-native';
import logger from '../utils/logger';

// Type definitions for react-native-fast-tflite
interface TFLiteModel {
  run: (input: Float32Array) => Float32Array;
  dispose: () => void;
}

interface TFLiteModule {
  loadModel: (modelPath: string) => Promise<TFLiteModel>;
  loadModelFromAsset: (assetName: string) => Promise<TFLiteModel>;
}

// Fallback for when TFLite is not available
let TFLite: TFLiteModule | null = null;

// Try to load TFLite module (will be null if not installed)
try {
  // @ts-ignore - react-native-fast-tflite may not be installed yet
  TFLite = require('react-native-fast-tflite').default;
} catch (e) {
  logger.warn('TensorFlow Lite not available. Install with: yarn add react-native-fast-tflite');
}

interface UseTensorFlowLiteOptions {
  modelPath?: string;
  assetName?: string;
  autoLoad?: boolean;
}

interface UseTensorFlowLiteReturn {
  model: TFLiteModel | null;
  loading: boolean;
  error: Error | null;
  loadModel: (path?: string, asset?: string) => Promise<void>;
  runInference: (features: number[]) => Promise<number | null>;
  isAvailable: boolean;
}

/**
 * Hook for TensorFlow Lite model loading and inference
 * 
 * Usage:
 * ```tsx
 * const { model, loading, runInference } = useTensorFlowLite({
 *   assetName: 'strategy_predictor.tflite',
 *   autoLoad: true
 * });
 * 
 * const probability = await runInference([volatility, volume, momentum, ...]);
 * ```
 */
export function useTensorFlowLite(options: UseTensorFlowLiteOptions = {}): UseTensorFlowLiteReturn {
  const { modelPath, assetName, autoLoad = false } = options;
  
  const [model, setModel] = useState<TFLiteModel | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const modelRef = useRef<TFLiteModel | null>(null);

  const isAvailable = TFLite !== null;

  const loadModel = async (path?: string, asset?: string) => {
    if (!TFLite) {
      const err = new Error('TensorFlow Lite not available. Install react-native-fast-tflite');
      setError(err);
      logger.error('TFLite not available');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      let loadedModel: TFLiteModel;

      if (asset) {
        // Load from app bundle (recommended for production)
        logger.log(`Loading TFLite model from asset: ${asset}`);
        loadedModel = await TFLite.loadModelFromAsset(asset);
      } else if (path) {
        // Load from file path
        logger.log(`Loading TFLite model from path: ${path}`);
        loadedModel = await TFLite.loadModel(path);
      } else if (assetName) {
        loadedModel = await TFLite.loadModelFromAsset(assetName);
      } else if (modelPath) {
        loadedModel = await TFLite.loadModel(modelPath);
      } else {
        throw new Error('No model path or asset name provided');
      }

      // Dispose old model if exists
      if (modelRef.current) {
        modelRef.current.dispose();
      }

      modelRef.current = loadedModel;
      setModel(loadedModel);
      logger.log('✅ TFLite model loaded successfully');
    } catch (err: any) {
      const error = err instanceof Error ? err : new Error(String(err));
      setError(error);
      logger.error('Failed to load TFLite model:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const runInference = async (features: number[]): Promise<number | null> => {
    if (!modelRef.current) {
      logger.warn('TFLite model not loaded. Cannot run inference.');
      return null;
    }

    try {
      // Convert features to Float32Array (required by TFLite)
      const inputTensor = new Float32Array(features);
      
      // Run inference
      const startTime = Date.now();
      const output = modelRef.current.run(inputTensor);
      const inferenceTime = Date.now() - startTime;

      // Parse output (assuming single output value - probability)
      const probability = output[0];
      
      logger.log(`TFLite inference completed in ${inferenceTime}ms. Probability: ${probability.toFixed(4)}`);
      
      return probability;
    } catch (err: any) {
      logger.error('TFLite inference error:', err);
      return null;
    }
  };

  // Auto-load model on mount if requested
  useEffect(() => {
    if (autoLoad && (modelPath || assetName) && !model && !loading && !error) {
      loadModel(modelPath, assetName);
    }
  }, [autoLoad, modelPath, assetName]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (modelRef.current) {
        modelRef.current.dispose();
        modelRef.current = null;
      }
    };
  }, []);

  return {
    model,
    loading,
    error,
    loadModel,
    runInference,
    isAvailable,
  };
}

