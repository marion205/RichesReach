#!/usr/bin/env python3
"""
Export and Quantize Finance-Specific Whisper Model
Merges LoRA adapter with base model and exports for Whisper.cpp deployment.
"""

import os
import torch
import json
from pathlib import Path
from typing import Dict, Optional
import logging
import subprocess
import shutil
from transformers import WhisperForConditionalGeneration, WhisperProcessor
from peft import PeftModel
import argparse

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FinanceModelExporter:
    """Export and quantize finance-specific Whisper model."""
    
    def __init__(self, 
                 base_model_path: str = "openai/whisper-tiny.en",
                 lora_model_path: str = "./whisper-finance-lora",
                 output_dir: str = "./whisper-finance-export"):
        self.base_model_path = base_model_path
        self.lora_model_path = lora_model_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Whisper.cpp paths
        self.whisper_cpp_dir = Path("./whisper.cpp")
        self.whisper_cpp_main = self.whisper_cpp_dir / "main"
        self.whisper_cpp_quantize = self.whisper_cpp_dir / "quantize"
        
    def merge_lora_model(self) -> str:
        """Merge LoRA adapter with base model."""
        logger.info("Merging LoRA adapter with base model...")
        
        # Load base model
        logger.info(f"Loading base model: {self.base_model_path}")
        base_model = WhisperForConditionalGeneration.from_pretrained(
            self.base_model_path,
            torch_dtype=torch.float32
        )
        
        # Load LoRA model
        logger.info(f"Loading LoRA model: {self.lora_model_path}")
        lora_model = PeftModel.from_pretrained(base_model, self.lora_model_path)
        
        # Merge and unload
        logger.info("Merging LoRA adapter...")
        merged_model = lora_model.merge_and_unload()
        
        # Save merged model
        merged_model_path = self.output_dir / "whisper-finance-merged"
        merged_model.save_pretrained(merged_model_path)
        
        # Save processor
        processor = WhisperProcessor.from_pretrained(self.lora_model_path)
        processor.save_pretrained(merged_model_path)
        
        logger.info(f"Merged model saved to: {merged_model_path}")
        return str(merged_model_path)
    
    def convert_to_ggml(self, model_path: str) -> str:
        """Convert merged model to GGML format for Whisper.cpp."""
        logger.info("Converting model to GGML format...")
        
        # Check if whisper.cpp exists
        if not self.whisper_cpp_dir.exists():
            logger.error("Whisper.cpp directory not found. Please clone whisper.cpp first.")
            raise FileNotFoundError("Whisper.cpp not found")
        
        # Convert model
        ggml_path = self.output_dir / "ggml-whisper-finance.bin"
        
        convert_cmd = [
            "python", str(self.whisper_cpp_dir / "convert-pt-to-ggml.py"),
            model_path,
            str(self.output_dir),
            "--output-format", "ggml"
        ]
        
        logger.info(f"Running conversion command: {' '.join(convert_cmd)}")
        
        try:
            result = subprocess.run(convert_cmd, check=True, capture_output=True, text=True)
            logger.info("Model conversion completed successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"Model conversion failed: {e}")
            logger.error(f"Error output: {e.stderr}")
            raise
        
        return str(ggml_path)
    
    def quantize_model(self, ggml_path: str, quantization_type: str = "q4_0") -> str:
        """Quantize GGML model for smaller size."""
        logger.info(f"Quantizing model with {quantization_type}...")
        
        # Check if quantize binary exists
        if not self.whisper_cpp_quantize.exists():
            logger.error("Whisper.cpp quantize binary not found. Please build whisper.cpp first.")
            raise FileNotFoundError("Quantize binary not found")
        
        # Quantized model path
        quantized_path = self.output_dir / f"ggml-whisper-finance-{quantization_type}.bin"
        
        # Run quantization
        quantize_cmd = [
            str(self.whisper_cpp_quantize),
            ggml_path,
            str(quantized_path),
            quantization_type
        ]
        
        logger.info(f"Running quantization command: {' '.join(quantize_cmd)}")
        
        try:
            result = subprocess.run(quantize_cmd, check=True, capture_output=True, text=True)
            logger.info("Model quantization completed successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"Model quantization failed: {e}")
            logger.error(f"Error output: {e.stderr}")
            raise
        
        return str(quantized_path)
    
    def create_model_info(self, 
                         merged_model_path: str,
                         quantized_path: str,
                         quantization_type: str) -> Dict:
        """Create model information file."""
        model_info = {
            "model_name": "whisper-finance-tuned",
            "base_model": self.base_model_path,
            "lora_model": self.lora_model_path,
            "merged_model": str(merged_model_path),
            "quantized_model": str(quantized_path),
            "quantization_type": quantization_type,
            "description": "Finance-specific fine-tuned Whisper model using LoRA",
            "training_data": "Financial conversations, terminology, and domain-specific audio",
            "performance": {
                "wer": "Expected <5% on financial audio",
                "cer": "Expected <2% on financial audio",
                "finance_wer": "Expected <3% on financial terminology"
            },
            "usage": {
                "whisper_cpp": f"./main -m {quantized_path} -f audio.wav --language en",
                "python": "Use with transformers library for inference"
            },
            "file_sizes": {
                "merged_model": self._get_file_size(merged_model_path),
                "quantized_model": self._get_file_size(quantized_path)
            }
        }
        
        # Save model info
        info_path = self.output_dir / "model_info.json"
        with open(info_path, 'w') as f:
            json.dump(model_info, f, indent=2)
        
        logger.info(f"Model information saved to: {info_path}")
        return model_info
    
    def _get_file_size(self, file_path: str) -> str:
        """Get human-readable file size."""
        if os.path.isfile(file_path):
            size = os.path.getsize(file_path)
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
            return f"{size:.1f} TB"
        else:
            return "Unknown"
    
    def test_quantized_model(self, quantized_path: str) -> bool:
        """Test the quantized model with a sample audio file."""
        logger.info("Testing quantized model...")
        
        # Check if main binary exists
        if not self.whisper_cpp_main.exists():
            logger.warning("Whisper.cpp main binary not found. Skipping test.")
            return False
        
        # Create a test audio file (sine wave)
        test_audio_path = self.output_dir / "test_audio.wav"
        self._create_test_audio(str(test_audio_path))
        
        # Test command
        test_cmd = [
            str(self.whisper_cpp_main),
            "-m", quantized_path,
            "-f", str(test_audio_path),
            "--language", "en",
            "--no-timestamps"
        ]
        
        logger.info(f"Running test command: {' '.join(test_cmd)}")
        
        try:
            result = subprocess.run(test_cmd, check=True, capture_output=True, text=True)
            logger.info("Model test completed successfully")
            logger.info(f"Test output: {result.stdout}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Model test failed: {e}")
            logger.error(f"Error output: {e.stderr}")
            return False
    
    def _create_test_audio(self, output_path: str, duration: float = 3.0, sample_rate: int = 16000):
        """Create a test audio file with a sine wave."""
        import numpy as np
        import soundfile as sf
        
        # Generate sine wave
        t = np.linspace(0, duration, int(sample_rate * duration))
        frequency = 440  # A4 note
        audio_data = 0.3 * np.sin(2 * np.pi * frequency * t)
        
        # Save audio file
        sf.write(output_path, audio_data, sample_rate)
        logger.info(f"Test audio created: {output_path}")
    
    def setup_whisper_cpp(self) -> bool:
        """Setup whisper.cpp if not already available."""
        if self.whisper_cpp_dir.exists():
            logger.info("Whisper.cpp already exists")
            return True
        
        logger.info("Setting up whisper.cpp...")
        
        # Clone whisper.cpp
        clone_cmd = [
            "git", "clone", 
            "https://github.com/ggerganov/whisper.cpp.git",
            str(self.whisper_cpp_dir)
        ]
        
        try:
            subprocess.run(clone_cmd, check=True)
            logger.info("Whisper.cpp cloned successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to clone whisper.cpp: {e}")
            return False
        
        # Build whisper.cpp
        build_cmd = ["make", "-C", str(self.whisper_cpp_dir)]
        
        try:
            subprocess.run(build_cmd, check=True)
            logger.info("Whisper.cpp built successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to build whisper.cpp: {e}")
            return False
        
        return True
    
    def export_model(self, quantization_type: str = "q4_0") -> Dict:
        """Complete model export pipeline."""
        logger.info("Starting model export pipeline...")
        
        # Setup whisper.cpp if needed
        if not self.setup_whisper_cpp():
            logger.error("Failed to setup whisper.cpp")
            return {}
        
        # Merge LoRA model
        merged_model_path = self.merge_lora_model()
        
        # Convert to GGML
        ggml_path = self.convert_to_ggml(merged_model_path)
        
        # Quantize model
        quantized_path = self.quantize_model(ggml_path, quantization_type)
        
        # Test quantized model
        test_success = self.test_quantized_model(quantized_path)
        
        # Create model info
        model_info = self.create_model_info(
            merged_model_path, 
            quantized_path, 
            quantization_type
        )
        
        # Add test results
        model_info["test_results"] = {
            "test_successful": test_success,
            "test_audio": str(self.output_dir / "test_audio.wav")
        }
        
        logger.info("Model export pipeline completed!")
        logger.info(f"Quantized model: {quantized_path}")
        logger.info(f"Model info: {self.output_dir / 'model_info.json'}")
        
        return model_info
    
    def create_deployment_package(self, quantized_path: str) -> str:
        """Create deployment package for the quantized model."""
        logger.info("Creating deployment package...")
        
        package_dir = self.output_dir / "deployment"
        package_dir.mkdir(exist_ok=True)
        
        # Copy quantized model
        model_name = Path(quantized_path).name
        shutil.copy2(quantized_path, package_dir / model_name)
        
        # Copy whisper.cpp binaries
        if self.whisper_cpp_main.exists():
            shutil.copy2(self.whisper_cpp_main, package_dir / "whisper")
        
        if self.whisper_cpp_quantize.exists():
            shutil.copy2(self.whisper_cpp_quantize, package_dir / "quantize")
        
        # Create deployment script
        deployment_script = package_dir / "deploy.sh"
        with open(deployment_script, 'w') as f:
            f.write(f"""#!/bin/bash
# Finance-Specific Whisper Model Deployment Script

MODEL_PATH="{model_name}"
AUDIO_FILE="$1"

if [ -z "$AUDIO_FILE" ]; then
    echo "Usage: $0 <audio_file>"
    echo "Example: $0 audio.wav"
    exit 1
fi

if [ ! -f "$AUDIO_FILE" ]; then
    echo "Error: Audio file '$AUDIO_FILE' not found"
    exit 1
fi

echo "Transcribing audio with finance-tuned Whisper model..."
./whisper -m "$MODEL_PATH" -f "$AUDIO_FILE" --language en --best-of 5

echo "Transcription completed!"
""")
        
        # Make script executable
        os.chmod(deployment_script, 0o755)
        
        # Create README
        readme_path = package_dir / "README.md"
        with open(readme_path, 'w') as f:
            f.write(f"""# Finance-Specific Whisper Model

This package contains a finance-tuned Whisper model optimized for financial terminology and conversations.

## Files

- `{model_name}`: Quantized finance-tuned Whisper model
- `whisper`: Whisper.cpp binary for inference
- `quantize`: Quantization utility
- `deploy.sh`: Deployment script

## Usage

### Command Line

```bash
./deploy.sh audio.wav
```

### Direct Usage

```bash
./whisper -m {model_name} -f audio.wav --language en --best-of 5
```

## Model Information

- Base Model: {self.base_model_path}
- Quantization: q4_0
- Optimized for: Financial terminology and conversations
- Expected WER: <5% on financial audio

## Performance

This model is specifically fine-tuned for financial domain and should provide:
- Better accuracy on financial terminology
- Improved transcription of investment discussions
- Enhanced performance on earnings calls and financial podcasts

## Requirements

- Linux/macOS
- Audio file in WAV, MP3, or M4A format
- 16kHz sample rate recommended
""")
        
        logger.info(f"Deployment package created: {package_dir}")
        return str(package_dir)

def main():
    """Main function for model export."""
    parser = argparse.ArgumentParser(description="Export and quantize finance-specific Whisper model")
    parser.add_argument("--base-model", default="openai/whisper-tiny.en", help="Base model path")
    parser.add_argument("--lora-model", default="./whisper-finance-lora", help="LoRA model path")
    parser.add_argument("--output-dir", default="./whisper-finance-export", help="Output directory")
    parser.add_argument("--quantization", default="q4_0", help="Quantization type")
    parser.add_argument("--create-package", action="store_true", help="Create deployment package")
    
    args = parser.parse_args()
    
    # Create exporter
    exporter = FinanceModelExporter(
        base_model_path=args.base_model,
        lora_model_path=args.lora_model,
        output_dir=args.output_dir
    )
    
    # Export model
    model_info = exporter.export_model(args.quantization)
    
    if model_info:
        logger.info("Model export completed successfully!")
        
        if args.create_package:
            package_dir = exporter.create_deployment_package(model_info["quantized_model"])
            logger.info(f"Deployment package created: {package_dir}")
    else:
        logger.error("Model export failed!")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
