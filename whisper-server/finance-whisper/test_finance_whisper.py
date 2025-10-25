#!/usr/bin/env python3
"""
Test Script for Finance-Specific Whisper Implementation
Validates dataset preparation, training, and export functionality.
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import logging
import subprocess
import time

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FinanceWhisperTester:
    """Test suite for finance-specific Whisper implementation."""
    
    def __init__(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="finance_whisper_test_"))
        self.results = {}
        
    def cleanup(self):
        """Clean up test directory."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_imports(self) -> bool:
        """Test if all required modules can be imported."""
        logger.info("Testing imports...")
        
        try:
            import torch
            import transformers
            import datasets
            import peft
            import jiwer
            import librosa
            import soundfile
            import numpy as np
            import pandas as pd
            
            logger.info("✅ All imports successful")
            return True
        except ImportError as e:
            logger.error(f"❌ Import failed: {e}")
            return False
    
    def test_dataset_preparation(self) -> bool:
        """Test dataset preparation functionality."""
        logger.info("Testing dataset preparation...")
        
        try:
            from prepare_finance_dataset import FinanceDatasetPreparer
            
            # Create preparer with test directory
            preparer = FinanceDatasetPreparer(str(self.test_dir / "test_dataset"))
            
            # Test synthetic data creation
            synthetic_data = preparer.create_synthetic_audio_dataset(num_samples=10)
            
            if len(synthetic_data) != 10:
                logger.error(f"❌ Expected 10 samples, got {len(synthetic_data)}")
                return False
            
            # Test terminology data creation
            terminology_data = preparer.create_finance_terminology_dataset()
            
            if len(terminology_data) == 0:
                logger.error("❌ No terminology data created")
                return False
            
            # Test dataset processing
            all_data = synthetic_data + terminology_data
            cleaned_data = preparer.process_and_clean_dataset(all_data)
            
            if len(cleaned_data) == 0:
                logger.error("❌ No cleaned data")
                return False
            
            # Test statistics generation
            stats = preparer.generate_dataset_statistics(cleaned_data)
            
            if stats["total_samples"] == 0:
                logger.error("❌ No samples in statistics")
                return False
            
            logger.info("✅ Dataset preparation test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Dataset preparation test failed: {e}")
            return False
    
    def test_training_config(self) -> bool:
        """Test training configuration."""
        logger.info("Testing training configuration...")
        
        try:
            from fine_tune_whisper import FinanceWhisperConfig
            
            # Test configuration creation
            config = FinanceWhisperConfig(
                model_name="openai/whisper-tiny.en",
                output_dir=str(self.test_dir / "test_training"),
                lora_r=8,  # Smaller for testing
                lora_alpha=16,
                learning_rate=1e-4,
                num_train_epochs=1,  # Short for testing
                per_device_train_batch_size=2,  # Small for testing
                use_wandb=False  # Disable for testing
            )
            
            # Test configuration validation
            if config.lora_r <= 0:
                logger.error("❌ Invalid LoRA rank")
                return False
            
            if config.learning_rate <= 0:
                logger.error("❌ Invalid learning rate")
                return False
            
            logger.info("✅ Training configuration test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Training configuration test failed: {e}")
            return False
    
    def test_model_loading(self) -> bool:
        """Test model loading functionality."""
        logger.info("Testing model loading...")
        
        try:
            from transformers import WhisperForConditionalGeneration, WhisperProcessor
            
            # Test processor loading
            processor = WhisperProcessor.from_pretrained("openai/whisper-tiny.en")
            
            if processor is None:
                logger.error("❌ Failed to load processor")
                return False
            
            # Test model loading
            model = WhisperForConditionalGeneration.from_pretrained(
                "openai/whisper-tiny.en",
                torch_dtype="auto"
            )
            
            if model is None:
                logger.error("❌ Failed to load model")
                return False
            
            logger.info("✅ Model loading test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Model loading test failed: {e}")
            return False
    
    def test_lora_setup(self) -> bool:
        """Test LoRA setup functionality."""
        logger.info("Testing LoRA setup...")
        
        try:
            from transformers import WhisperForConditionalGeneration
            from peft import LoraConfig, get_peft_model, TaskType
            
            # Load model
            model = WhisperForConditionalGeneration.from_pretrained(
                "openai/whisper-tiny.en",
                torch_dtype="auto"
            )
            
            # Setup LoRA config
            lora_config = LoraConfig(
                task_type=TaskType.SEQ_2_SEQ_LM,
                inference_mode=False,
                r=8,
                lora_alpha=16,
                lora_dropout=0.1,
                target_modules=["q_proj", "v_proj", "k_proj", "o_proj"]
            )
            
            # Apply LoRA
            peft_model = get_peft_model(model, lora_config)
            
            if peft_model is None:
                logger.error("❌ Failed to create PEFT model")
                return False
            
            # Test trainable parameters
            peft_model.print_trainable_parameters()
            
            logger.info("✅ LoRA setup test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ LoRA setup test failed: {e}")
            return False
    
    def test_export_functionality(self) -> bool:
        """Test export functionality."""
        logger.info("Testing export functionality...")
        
        try:
            from export_finance_model import FinanceModelExporter
            
            # Create exporter
            exporter = FinanceModelExporter(
                base_model_path="openai/whisper-tiny.en",
                lora_model_path="nonexistent",  # Won't actually merge
                output_dir=str(self.test_dir / "test_export")
            )
            
            # Test directory creation
            if not exporter.output_dir.exists():
                logger.error("❌ Export directory not created")
                return False
            
            # Test file size calculation
            test_file = self.test_dir / "test_file.txt"
            test_file.write_text("test content")
            
            file_size = exporter._get_file_size(str(test_file))
            
            if file_size == "Unknown":
                logger.error("❌ File size calculation failed")
                return False
            
            logger.info("✅ Export functionality test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Export functionality test failed: {e}")
            return False
    
    def test_configuration_loading(self) -> bool:
        """Test configuration loading."""
        logger.info("Testing configuration loading...")
        
        try:
            # Create test config
            test_config = {
                "dataset": {
                    "output_dir": "./test_dataset",
                    "num_synthetic_samples": 100
                },
                "training": {
                    "model_name": "openai/whisper-tiny.en",
                    "lora_r": 16,
                    "learning_rate": 1e-4
                },
                "export": {
                    "quantization_type": "q4_0"
                }
            }
            
            config_path = self.test_dir / "test_config.json"
            with open(config_path, 'w') as f:
                json.dump(test_config, f)
            
            # Test loading
            with open(config_path, 'r') as f:
                loaded_config = json.load(f)
            
            if loaded_config["dataset"]["num_synthetic_samples"] != 100:
                logger.error("❌ Configuration loading failed")
                return False
            
            logger.info("✅ Configuration loading test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Configuration loading test failed: {e}")
            return False
    
    def test_audio_processing(self) -> bool:
        """Test audio processing functionality."""
        logger.info("Testing audio processing...")
        
        try:
            import librosa
            import soundfile as sf
            import numpy as np
            
            # Create test audio
            sample_rate = 16000
            duration = 1.0
            t = np.linspace(0, duration, int(sample_rate * duration))
            audio_data = 0.3 * np.sin(2 * np.pi * 440 * t)
            
            # Save audio
            audio_path = self.test_dir / "test_audio.wav"
            sf.write(audio_path, audio_data, sample_rate)
            
            # Load audio
            loaded_audio, loaded_sr = librosa.load(audio_path, sr=sample_rate)
            
            if loaded_sr != sample_rate:
                logger.error("❌ Sample rate mismatch")
                return False
            
            if len(loaded_audio) != len(audio_data):
                logger.error("❌ Audio length mismatch")
                return False
            
            logger.info("✅ Audio processing test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Audio processing test failed: {e}")
            return False
    
    def test_finance_terminology(self) -> bool:
        """Test finance terminology functionality."""
        logger.info("Testing finance terminology...")
        
        try:
            from prepare_finance_dataset import FinanceDatasetPreparer
            
            preparer = FinanceDatasetPreparer()
            
            # Test finance terms list
            if len(preparer.finance_terms) == 0:
                logger.error("❌ No finance terms defined")
                return False
            
            # Test financial conversations
            if len(preparer.financial_conversations) == 0:
                logger.error("❌ No financial conversations defined")
                return False
            
            # Test text variation
            original_text = "I'm looking to diversify my portfolio"
            varied_text = preparer._add_text_variation(original_text)
            
            if len(varied_text) == 0:
                logger.error("❌ Text variation failed")
                return False
            
            logger.info("✅ Finance terminology test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Finance terminology test failed: {e}")
            return False
    
    def run_all_tests(self) -> bool:
        """Run all tests."""
        logger.info("Running Finance-Specific Whisper Tests")
        logger.info("=" * 50)
        
        tests = [
            ("Imports", self.test_imports),
            ("Dataset Preparation", self.test_dataset_preparation),
            ("Training Configuration", self.test_training_config),
            ("Model Loading", self.test_model_loading),
            ("LoRA Setup", self.test_lora_setup),
            ("Export Functionality", self.test_export_functionality),
            ("Configuration Loading", self.test_configuration_loading),
            ("Audio Processing", self.test_audio_processing),
            ("Finance Terminology", self.test_finance_terminology),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            logger.info(f"\n--- {test_name} ---")
            try:
                if test_func():
                    passed += 1
                    self.results[test_name] = "PASSED"
                else:
                    self.results[test_name] = "FAILED"
            except Exception as e:
                logger.error(f"❌ {test_name} test crashed: {e}")
                self.results[test_name] = "CRASHED"
        
        # Print results
        logger.info("\n" + "=" * 50)
        logger.info("TEST RESULTS")
        logger.info("=" * 50)
        
        for test_name, result in self.results.items():
            status = "✅" if result == "PASSED" else "❌"
            logger.info(f"{status} {test_name}: {result}")
        
        logger.info(f"\nTotal: {passed}/{total} tests passed")
        
        if passed == total:
            logger.info("🎉 All tests passed! Finance-Specific Whisper is ready to use.")
            return True
        else:
            logger.error(f"❌ {total - passed} tests failed. Please check the errors above.")
            return False
    
    def save_results(self):
        """Save test results to file."""
        results_path = self.test_dir / "test_results.json"
        with open(results_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"Test results saved to: {results_path}")

def main():
    """Main test function."""
    tester = FinanceWhisperTester()
    
    try:
        success = tester.run_all_tests()
        tester.save_results()
        return 0 if success else 1
    finally:
        tester.cleanup()

if __name__ == "__main__":
    exit(main())
