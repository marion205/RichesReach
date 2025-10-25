#!/usr/bin/env python3
"""
Finance-Specific Whisper Fine-Tuning with LoRA
Implements Parameter-Efficient Fine-Tuning (PEFT) using LoRA for Whisper models.
"""

import os
import torch
import torchaudio
from transformers import (
    WhisperForConditionalGeneration,
    WhisperTokenizer,
    WhisperProcessor,
    Seq2SeqTrainingArguments,
    Seq2SeqTrainer,
    get_linear_schedule_with_warmup,
)
from peft import LoraConfig, get_peft_model, TaskType, PeftModel
from datasets import load_dataset, Dataset
import numpy as np
from jiwer import wer, cer
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json
from tqdm import tqdm
import wandb
from dataclasses import dataclass, field

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class FinanceWhisperConfig:
    """Configuration for finance-specific Whisper fine-tuning."""
    
    # Model configuration
    model_name: str = "openai/whisper-tiny.en"
    output_dir: str = "./whisper-finance-lora"
    
    # LoRA configuration
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.1
    target_modules: List[str] = field(default_factory=lambda: [
        "q_proj", "v_proj", "k_proj", "o_proj", "gate_proj", "up_proj", "down_proj"
    ])
    
    # Training configuration
    learning_rate: float = 1e-4
    num_train_epochs: int = 3
    per_device_train_batch_size: int = 8
    per_device_eval_batch_size: int = 8
    gradient_accumulation_steps: int = 1
    warmup_steps: int = 500
    max_steps: int = 4000
    
    # Evaluation configuration
    evaluation_strategy: str = "steps"
    eval_steps: int = 500
    save_steps: int = 500
    logging_steps: int = 100
    
    # Generation configuration
    generation_max_length: int = 225
    predict_with_generate: bool = True
    
    # Hardware configuration
    fp16: bool = True
    dataloader_num_workers: int = 4
    remove_unused_columns: bool = False
    
    # Dataset configuration
    dataset_path: str = "./finance_dataset/huggingface_dataset"
    train_split: float = 0.9
    test_split: float = 0.1
    
    # Finance-specific configuration
    finance_terms_weight: float = 2.0  # Higher weight for financial terms
    min_audio_length: float = 0.5
    max_audio_length: float = 30.0
    
    # Logging configuration
    use_wandb: bool = True
    wandb_project: str = "whisper-finance-finetuning"
    wandb_run_name: Optional[str] = None

class FinanceWhisperTrainer:
    """Finance-specific Whisper fine-tuning trainer."""
    
    def __init__(self, config: FinanceWhisperConfig):
        self.config = config
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Initialize components
        self.processor = None
        self.tokenizer = None
        self.model = None
        self.peft_model = None
        self.trainer = None
        
        # Setup logging
        if config.use_wandb:
            wandb.init(
                project=config.wandb_project,
                name=config.wandb_run_name or f"whisper-finance-{config.model_name.split('/')[-1]}",
                config=config.__dict__
            )
    
    def setup_model_and_processor(self):
        """Setup Whisper model and processor."""
        logger.info(f"Loading model: {self.config.model_name}")
        
        # Load processor and tokenizer
        self.processor = WhisperProcessor.from_pretrained(self.config.model_name)
        self.tokenizer = WhisperTokenizer.from_pretrained(self.config.model_name)
        
        # Load model
        self.model = WhisperForConditionalGeneration.from_pretrained(
            self.config.model_name,
            torch_dtype=torch.float16 if self.config.fp16 else torch.float32
        )
        
        # Setup LoRA configuration
        lora_config = LoraConfig(
            task_type=TaskType.SEQ_2_SEQ_LM,
            inference_mode=False,
            r=self.config.lora_r,
            lora_alpha=self.config.lora_alpha,
            lora_dropout=self.config.lora_dropout,
            target_modules=self.config.target_modules,
        )
        
        # Apply LoRA to model
        self.peft_model = get_peft_model(self.model, lora_config)
        
        # Print trainable parameters
        self.peft_model.print_trainable_parameters()
        
        logger.info("Model and processor setup completed")
    
    def load_finance_dataset(self) -> Tuple[Dataset, Dataset]:
        """Load and prepare finance dataset."""
        logger.info(f"Loading dataset from {self.config.dataset_path}")
        
        # Load dataset
        dataset = load_dataset("json", data_files=f"{self.config.dataset_path}/finance_dataset.jsonl")["train"]
        
        # Split dataset
        dataset = dataset.train_test_split(
            test_size=self.config.test_split,
            seed=42
        )
        
        train_dataset = dataset["train"]
        eval_dataset = dataset["test"]
        
        logger.info(f"Train samples: {len(train_dataset)}")
        logger.info(f"Eval samples: {len(eval_dataset)}")
        
        return train_dataset, eval_dataset
    
    def prepare_dataset(self, dataset: Dataset) -> Dataset:
        """Prepare dataset for training."""
        logger.info("Preparing dataset for training...")
        
        def prepare_batch(batch):
            """Prepare a batch of data for training."""
            # Load audio
            audio = batch["audio"]
            
            # Process audio
            input_features = self.processor(
                audio["array"], 
                sampling_rate=audio["sampling_rate"]
            ).input_features[0]
            
            # Process text
            labels = self.tokenizer(batch["text"]).input_ids
            
            # Add finance term weighting
            finance_weight = self._calculate_finance_weight(batch["text"])
            
            return {
                "input_features": input_features,
                "labels": labels,
                "finance_weight": finance_weight
            }
        
        # Apply preparation
        prepared_dataset = dataset.map(
            prepare_batch,
            remove_columns=dataset.column_names,
            desc="Preparing dataset"
        )
        
        return prepared_dataset
    
    def _calculate_finance_weight(self, text: str) -> float:
        """Calculate weight for financial terms in the text."""
        finance_terms = [
            "portfolio", "diversification", "asset allocation", "risk management",
            "volatility", "beta", "alpha", "sharpe ratio", "return on investment",
            "dividend yield", "price-to-earnings ratio", "market capitalization",
            "earnings per share", "book value", "debt-to-equity ratio",
            "bull market", "bear market", "market correction", "recession",
            "inflation", "deflation", "interest rates", "federal reserve",
            "quantitative easing", "monetary policy", "fiscal policy",
            "liquidity", "leverage", "margin", "short selling", "options",
            "futures", "derivatives", "hedge fund", "mutual fund", "etf",
            "credit score", "mortgage", "refinancing", "amortization",
            "compound interest", "annual percentage rate", "prime rate",
            "treasury bonds", "corporate bonds", "junk bonds", "yield curve",
            "tax deduction", "tax credit", "capital gains", "tax loss harvesting",
            "roth ira", "traditional ira", "401k", "403b", "hsa",
            "standard deduction", "itemized deduction", "tax bracket",
            "appreciation", "depreciation", "equity", "lien", "escrow",
            "closing costs", "down payment", "private mortgage insurance",
            "home equity loan", "reverse mortgage", "cap rate",
            "bitcoin", "ethereum", "blockchain", "cryptocurrency", "defi",
            "nft", "smart contract", "mining", "staking", "wallet",
            "exchange", "cold storage", "hot wallet", "private key",
            "revenue", "profit margin", "ebitda", "cash flow", "balance sheet",
            "income statement", "cash flow statement", "audit", "compliance",
            "due diligence", "merger", "acquisition", "ipo", "valuation"
        ]
        
        text_lower = text.lower()
        finance_term_count = sum(1 for term in finance_terms if term in text_lower)
        
        # Calculate weight based on finance term density
        if finance_term_count > 0:
            return min(self.config.finance_terms_weight, 1.0 + (finance_term_count * 0.1))
        else:
            return 1.0
    
    def setup_training_arguments(self) -> Seq2SeqTrainingArguments:
        """Setup training arguments."""
        return Seq2SeqTrainingArguments(
            output_dir=self.config.output_dir,
            per_device_train_batch_size=self.config.per_device_train_batch_size,
            per_device_eval_batch_size=self.config.per_device_eval_batch_size,
            gradient_accumulation_steps=self.config.gradient_accumulation_steps,
            learning_rate=self.config.learning_rate,
            num_train_epochs=self.config.num_train_epochs,
            max_steps=self.config.max_steps,
            warmup_steps=self.config.warmup_steps,
            evaluation_strategy=self.config.evaluation_strategy,
            eval_steps=self.config.eval_steps,
            save_steps=self.config.save_steps,
            logging_steps=self.config.logging_steps,
            generation_max_length=self.config.generation_max_length,
            predict_with_generate=self.config.predict_with_generate,
            fp16=self.config.fp16,
            dataloader_num_workers=self.config.dataloader_num_workers,
            remove_unused_columns=self.config.remove_unused_columns,
            load_best_model_at_end=True,
            metric_for_best_model="wer",
            greater_is_better=False,
            report_to="wandb" if self.config.use_wandb else None,
            run_name=self.config.wandb_run_name,
        )
    
    def compute_metrics(self, eval_pred):
        """Compute evaluation metrics."""
        predictions, labels = eval_pred
        
        # Decode predictions
        decoded_preds = self.tokenizer.batch_decode(predictions, skip_special_tokens=True)
        
        # Replace -100 in labels with pad token id
        labels = np.where(labels != -100, labels, self.tokenizer.pad_token_id)
        decoded_labels = self.tokenizer.batch_decode(labels, skip_special_tokens=True)
        
        # Compute WER and CER
        wer_score = wer(decoded_labels, decoded_preds)
        cer_score = cer(decoded_labels, decoded_preds)
        
        # Compute finance-specific metrics
        finance_wer = self._compute_finance_wer(decoded_labels, decoded_preds)
        
        return {
            "wer": wer_score,
            "cer": cer_score,
            "finance_wer": finance_wer
        }
    
    def _compute_finance_wer(self, references: List[str], predictions: List[str]) -> float:
        """Compute WER specifically for financial terms."""
        finance_terms = [
            "portfolio", "diversification", "asset allocation", "risk management",
            "volatility", "beta", "alpha", "sharpe ratio", "return on investment",
            "dividend yield", "price-to-earnings ratio", "market capitalization",
            "earnings per share", "book value", "debt-to-equity ratio",
            "bull market", "bear market", "market correction", "recession",
            "inflation", "deflation", "interest rates", "federal reserve",
            "quantitative easing", "monetary policy", "fiscal policy",
            "liquidity", "leverage", "margin", "short selling", "options",
            "futures", "derivatives", "hedge fund", "mutual fund", "etf",
            "credit score", "mortgage", "refinancing", "amortization",
            "compound interest", "annual percentage rate", "prime rate",
            "treasury bonds", "corporate bonds", "junk bonds", "yield curve",
            "tax deduction", "tax credit", "capital gains", "tax loss harvesting",
            "roth ira", "traditional ira", "401k", "403b", "hsa",
            "standard deduction", "itemized deduction", "tax bracket",
            "appreciation", "depreciation", "equity", "lien", "escrow",
            "closing costs", "down payment", "private mortgage insurance",
            "home equity loan", "reverse mortgage", "cap rate",
            "bitcoin", "ethereum", "blockchain", "cryptocurrency", "defi",
            "nft", "smart contract", "mining", "staking", "wallet",
            "exchange", "cold storage", "hot wallet", "private key",
            "revenue", "profit margin", "ebitda", "cash flow", "balance sheet",
            "income statement", "cash flow statement", "audit", "compliance",
            "due diligence", "merger", "acquisition", "ipo", "valuation"
        ]
        
        finance_refs = []
        finance_preds = []
        
        for ref, pred in zip(references, predictions):
            # Extract financial terms from reference and prediction
            ref_terms = [term for term in finance_terms if term in ref.lower()]
            pred_terms = [term for term in finance_terms if term in pred.lower()]
            
            if ref_terms or pred_terms:
                finance_refs.append(" ".join(ref_terms))
                finance_preds.append(" ".join(pred_terms))
        
        if finance_refs and finance_preds:
            return wer(finance_refs, finance_preds)
        else:
            return 0.0
    
    def setup_trainer(self, train_dataset: Dataset, eval_dataset: Dataset):
        """Setup the trainer."""
        logger.info("Setting up trainer...")
        
        # Setup training arguments
        training_args = self.setup_training_arguments()
        
        # Create trainer
        self.trainer = Seq2SeqTrainer(
            model=self.peft_model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            tokenizer=self.processor.feature_extractor,
            compute_metrics=self.compute_metrics,
        )
        
        logger.info("Trainer setup completed")
    
    def train(self):
        """Start training."""
        logger.info("Starting training...")
        
        # Setup model and processor
        self.setup_model_and_processor()
        
        # Load dataset
        train_dataset, eval_dataset = self.load_finance_dataset()
        
        # Prepare datasets
        train_dataset = self.prepare_dataset(train_dataset)
        eval_dataset = self.prepare_dataset(eval_dataset)
        
        # Setup trainer
        self.setup_trainer(train_dataset, eval_dataset)
        
        # Start training
        self.trainer.train()
        
        # Save final model
        self.trainer.save_model()
        
        logger.info("Training completed!")
    
    def evaluate(self, eval_dataset: Optional[Dataset] = None):
        """Evaluate the model."""
        if eval_dataset is None:
            _, eval_dataset = self.load_finance_dataset()
            eval_dataset = self.prepare_dataset(eval_dataset)
        
        logger.info("Evaluating model...")
        
        results = self.trainer.evaluate(eval_dataset)
        
        logger.info("Evaluation results:")
        for key, value in results.items():
            logger.info(f"{key}: {value}")
        
        return results
    
    def save_model(self, output_path: str):
        """Save the fine-tuned model."""
        logger.info(f"Saving model to {output_path}")
        
        # Save PEFT model
        self.peft_model.save_pretrained(output_path)
        
        # Save processor and tokenizer
        self.processor.save_pretrained(output_path)
        self.tokenizer.save_pretrained(output_path)
        
        # Save configuration
        config_path = os.path.join(output_path, "finance_config.json")
        with open(config_path, 'w') as f:
            json.dump(self.config.__dict__, f, indent=2)
        
        logger.info("Model saved successfully")

def main():
    """Main function for finance-specific Whisper fine-tuning."""
    
    # Configuration
    config = FinanceWhisperConfig(
        model_name="openai/whisper-tiny.en",
        output_dir="./whisper-finance-lora",
        lora_r=16,
        lora_alpha=32,
        learning_rate=1e-4,
        num_train_epochs=3,
        per_device_train_batch_size=8,
        use_wandb=True,
        wandb_project="whisper-finance-finetuning",
        wandb_run_name="whisper-tiny-finance-lora"
    )
    
    # Create trainer
    trainer = FinanceWhisperTrainer(config)
    
    # Train model
    trainer.train()
    
    # Evaluate model
    results = trainer.evaluate()
    
    # Save model
    trainer.save_model(config.output_dir)
    
    logger.info("Finance-specific Whisper fine-tuning completed!")

if __name__ == "__main__":
    main()
