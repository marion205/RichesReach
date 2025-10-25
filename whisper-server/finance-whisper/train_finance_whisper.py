#!/usr/bin/env python3
"""
Complete Finance-Specific Whisper Training Pipeline
Orchestrates dataset preparation, LoRA fine-tuning, and model export.
"""

import os
import sys
import argparse
import logging
from pathlib import Path
import json
import time
from typing import Dict, Optional

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from prepare_finance_dataset import FinanceDatasetPreparer
from fine_tune_whisper import FinanceWhisperTrainer, FinanceWhisperConfig
from export_finance_model import FinanceModelExporter

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FinanceWhisperPipeline:
    """Complete pipeline for finance-specific Whisper training."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.setup_directories()
        
    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Load configuration from file or use defaults."""
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        else:
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """Get default configuration."""
        return {
            "dataset": {
                "output_dir": "./finance_dataset",
                "num_synthetic_samples": 1000,
                "include_terminology": True,
                "include_external": False
            },
            "training": {
                "model_name": "openai/whisper-tiny.en",
                "output_dir": "./whisper-finance-lora",
                "lora_r": 16,
                "lora_alpha": 32,
                "lora_dropout": 0.1,
                "learning_rate": 1e-4,
                "num_train_epochs": 3,
                "per_device_train_batch_size": 8,
                "use_wandb": True,
                "wandb_project": "whisper-finance-finetuning"
            },
            "export": {
                "output_dir": "./whisper-finance-export",
                "quantization_type": "q4_0",
                "create_package": True
            }
        }
    
    def setup_directories(self):
        """Setup required directories."""
        dirs = [
            self.config["dataset"]["output_dir"],
            self.config["training"]["output_dir"],
            self.config["export"]["output_dir"]
        ]
        
        for dir_path in dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    def prepare_dataset(self) -> str:
        """Prepare finance-specific dataset."""
        logger.info("=== Step 1: Preparing Finance Dataset ===")
        
        dataset_config = self.config["dataset"]
        preparer = FinanceDatasetPreparer(dataset_config["output_dir"])
        
        # Create synthetic dataset
        synthetic_data = preparer.create_synthetic_audio_dataset(
            num_samples=dataset_config["num_synthetic_samples"]
        )
        
        # Create terminology dataset
        terminology_data = []
        if dataset_config["include_terminology"]:
            terminology_data = preparer.create_finance_terminology_dataset()
        
        # Load external datasets
        external_data = []
        if dataset_config["include_external"]:
            external_data = preparer.load_external_finance_datasets()
        
        # Combine all datasets
        all_data = synthetic_data + terminology_data + external_data
        
        # Process and clean
        cleaned_data = preparer.process_and_clean_dataset(all_data)
        
        # Save dataset
        preparer.save_dataset(cleaned_data)
        
        # Create Hugging Face dataset
        hf_dataset = preparer.create_huggingface_dataset(cleaned_data)
        hf_dataset.save_to_disk(str(Path(dataset_config["output_dir"]) / "huggingface_dataset"))
        
        # Generate statistics
        stats = preparer.generate_dataset_statistics(cleaned_data)
        
        # Save statistics
        stats_path = Path(dataset_config["output_dir"]) / "dataset_statistics.json"
        with open(stats_path, 'w') as f:
            json.dump(stats, f, indent=2)
        
        logger.info(f"Dataset prepared: {len(cleaned_data)} samples")
        logger.info(f"Total duration: {stats['total_hours']:.2f} hours")
        logger.info(f"Dataset saved to: {dataset_config['output_dir']}")
        
        return dataset_config["output_dir"]
    
    def train_model(self, dataset_path: str) -> str:
        """Train finance-specific Whisper model."""
        logger.info("=== Step 2: Training Finance-Specific Model ===")
        
        training_config = self.config["training"]
        
        # Create training configuration
        config = FinanceWhisperConfig(
            model_name=training_config["model_name"],
            output_dir=training_config["output_dir"],
            lora_r=training_config["lora_r"],
            lora_alpha=training_config["lora_alpha"],
            lora_dropout=training_config["lora_dropout"],
            learning_rate=training_config["learning_rate"],
            num_train_epochs=training_config["num_train_epochs"],
            per_device_train_batch_size=training_config["per_device_train_batch_size"],
            use_wandb=training_config["use_wandb"],
            wandb_project=training_config["wandb_project"],
            dataset_path=dataset_path
        )
        
        # Create trainer
        trainer = FinanceWhisperTrainer(config)
        
        # Train model
        trainer.train()
        
        # Evaluate model
        results = trainer.evaluate()
        
        # Save model
        trainer.save_model(training_config["output_dir"])
        
        # Save training results
        results_path = Path(training_config["output_dir"]) / "training_results.json"
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Training completed!")
        logger.info(f"Final WER: {results.get('eval_wer', 'N/A')}")
        logger.info(f"Final CER: {results.get('eval_cer', 'N/A')}")
        logger.info(f"Finance WER: {results.get('eval_finance_wer', 'N/A')}")
        logger.info(f"Model saved to: {training_config['output_dir']}")
        
        return training_config["output_dir"]
    
    def export_model(self, lora_model_path: str) -> str:
        """Export and quantize the trained model."""
        logger.info("=== Step 3: Exporting and Quantizing Model ===")
        
        export_config = self.config["export"]
        
        # Create exporter
        exporter = FinanceModelExporter(
            base_model_path=self.config["training"]["model_name"],
            lora_model_path=lora_model_path,
            output_dir=export_config["output_dir"]
        )
        
        # Export model
        model_info = exporter.export_model(export_config["quantization_type"])
        
        if not model_info:
            raise RuntimeError("Model export failed!")
        
        # Create deployment package
        if export_config["create_package"]:
            package_dir = exporter.create_deployment_package(model_info["quantized_model"])
            logger.info(f"Deployment package created: {package_dir}")
        
        # Save model info
        info_path = Path(export_config["output_dir"]) / "model_info.json"
        with open(info_path, 'w') as f:
            json.dump(model_info, f, indent=2)
        
        logger.info(f"Model export completed!")
        logger.info(f"Quantized model: {model_info['quantized_model']}")
        logger.info(f"Model size: {model_info['file_sizes']['quantized_model']}")
        logger.info(f"Test successful: {model_info['test_results']['test_successful']}")
        
        return export_config["output_dir"]
    
    def run_pipeline(self) -> Dict:
        """Run the complete training pipeline."""
        logger.info("Starting Finance-Specific Whisper Training Pipeline")
        logger.info("=" * 60)
        
        start_time = time.time()
        results = {}
        
        try:
            # Step 1: Prepare dataset
            dataset_path = self.prepare_dataset()
            results["dataset_path"] = dataset_path
            
            # Step 2: Train model
            lora_model_path = self.train_model(dataset_path)
            results["lora_model_path"] = lora_model_path
            
            # Step 3: Export model
            export_path = self.export_model(lora_model_path)
            results["export_path"] = export_path
            
            # Calculate total time
            total_time = time.time() - start_time
            results["total_time"] = total_time
            
            logger.info("=" * 60)
            logger.info("Pipeline completed successfully!")
            logger.info(f"Total time: {total_time:.2f} seconds ({total_time/60:.2f} minutes)")
            logger.info(f"Dataset: {dataset_path}")
            logger.info(f"LoRA Model: {lora_model_path}")
            logger.info(f"Export: {export_path}")
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            raise
        
        return results
    
    def save_pipeline_results(self, results: Dict):
        """Save pipeline results."""
        results_path = Path(self.config["export"]["output_dir"]) / "pipeline_results.json"
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Pipeline results saved to: {results_path}")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Finance-Specific Whisper Training Pipeline")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--dataset-only", action="store_true", help="Only prepare dataset")
    parser.add_argument("--train-only", action="store_true", help="Only train model")
    parser.add_argument("--export-only", action="store_true", help="Only export model")
    parser.add_argument("--lora-model", help="Path to LoRA model for export-only mode")
    
    args = parser.parse_args()
    
    # Create pipeline
    pipeline = FinanceWhisperPipeline(args.config)
    
    try:
        if args.dataset_only:
            # Only prepare dataset
            dataset_path = pipeline.prepare_dataset()
            logger.info(f"Dataset preparation completed: {dataset_path}")
            
        elif args.train_only:
            # Only train model
            dataset_path = pipeline.config["dataset"]["output_dir"]
            lora_model_path = pipeline.train_model(dataset_path)
            logger.info(f"Training completed: {lora_model_path}")
            
        elif args.export_only:
            # Only export model
            if not args.lora_model:
                logger.error("--lora-model required for export-only mode")
                return 1
            
            export_path = pipeline.export_model(args.lora_model)
            logger.info(f"Export completed: {export_path}")
            
        else:
            # Run complete pipeline
            results = pipeline.run_pipeline()
            pipeline.save_pipeline_results(results)
            
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
