#!/usr/bin/env python3
"""
Finance-Specific Dataset Preparation for Whisper Fine-Tuning
Creates a curated dataset of financial audio and transcripts for domain-specific training.
"""

import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple
import librosa
import soundfile as sf
from datasets import Dataset, Audio
import re
from tqdm import tqdm
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FinanceDatasetPreparer:
    def __init__(self, output_dir: str = "finance_dataset"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Financial terminology patterns
        self.finance_terms = [
            # Investment Terms
            "portfolio", "diversification", "asset allocation", "risk management",
            "volatility", "beta", "alpha", "sharpe ratio", "return on investment",
            "dividend yield", "price-to-earnings ratio", "market capitalization",
            "earnings per share", "book value", "debt-to-equity ratio",
            
            # Trading Terms
            "bull market", "bear market", "market correction", "recession",
            "inflation", "deflation", "interest rates", "federal reserve",
            "quantitative easing", "monetary policy", "fiscal policy",
            "liquidity", "leverage", "margin", "short selling", "options",
            "futures", "derivatives", "hedge fund", "mutual fund", "etf",
            
            # Banking Terms
            "credit score", "mortgage", "refinancing", "amortization",
            "compound interest", "annual percentage rate", "prime rate",
            "treasury bonds", "corporate bonds", "junk bonds", "yield curve",
            
            # Tax Terms
            "tax deduction", "tax credit", "capital gains", "tax loss harvesting",
            "roth ira", "traditional ira", "401k", "403b", "hsa",
            "standard deduction", "itemized deduction", "tax bracket",
            
            # Real Estate Terms
            "appreciation", "depreciation", "equity", "lien", "escrow",
            "closing costs", "down payment", "private mortgage insurance",
            "home equity loan", "reverse mortgage", "cap rate",
            
            # Cryptocurrency Terms
            "bitcoin", "ethereum", "blockchain", "cryptocurrency", "defi",
            "nft", "smart contract", "mining", "staking", "wallet",
            "exchange", "cold storage", "hot wallet", "private key",
            
            # Business Terms
            "revenue", "profit margin", "ebitda", "cash flow", "balance sheet",
            "income statement", "cash flow statement", "audit", "compliance",
            "due diligence", "merger", "acquisition", "ipo", "valuation"
        ]
        
        # Create synthetic financial conversations
        self.financial_conversations = self._create_financial_conversations()
        
    def _create_financial_conversations(self) -> List[Dict[str, str]]:
        """Create synthetic financial conversations for training."""
        conversations = [
            {
                "text": "I'm looking to diversify my portfolio with some international exposure. What do you think about emerging markets?",
                "category": "investment_advice"
            },
            {
                "text": "The Federal Reserve just announced another interest rate hike. This will impact mortgage rates and bond yields significantly.",
                "category": "market_analysis"
            },
            {
                "text": "I need to do some tax loss harvesting before the end of the year. Can you help me identify which positions to sell?",
                "category": "tax_planning"
            },
            {
                "text": "My 401k is currently allocated 60% stocks, 30% bonds, and 10% alternatives. Should I rebalance given the current market volatility?",
                "category": "retirement_planning"
            },
            {
                "text": "The company's EBITDA margin has improved to 15% this quarter, but the debt-to-equity ratio is still concerning at 2.5.",
                "category": "financial_analysis"
            },
            {
                "text": "I'm considering a Roth IRA conversion, but I need to understand the tax implications and the five-year rule.",
                "category": "retirement_planning"
            },
            {
                "text": "The yield curve is inverted, which historically signals a potential recession. Should I adjust my asset allocation?",
                "category": "market_analysis"
            },
            {
                "text": "I want to start dollar-cost averaging into index funds. What's the optimal frequency and amount for my situation?",
                "category": "investment_strategy"
            },
            {
                "text": "My credit score is 720, and I'm looking to refinance my mortgage. Current rates are around 6.5% for a 30-year fixed.",
                "category": "mortgage_advice"
            },
            {
                "text": "The cryptocurrency market has been volatile. I'm thinking about allocating 5% of my portfolio to Bitcoin and Ethereum.",
                "category": "alternative_investments"
            },
            {
                "text": "I need to calculate my net worth for a loan application. Should I include my home equity and retirement accounts?",
                "category": "financial_planning"
            },
            {
                "text": "The company's price-to-earnings ratio is 18, which seems reasonable compared to the industry average of 22.",
                "category": "valuation_analysis"
            },
            {
                "text": "I'm considering a home equity line of credit for home improvements. What are the current rates and terms?",
                "category": "real_estate_financing"
            },
            {
                "text": "My HSA balance has grown to $15,000. Should I invest it in mutual funds or keep it in cash for medical expenses?",
                "category": "health_savings"
            },
            {
                "text": "The inflation rate is 3.2%, which is above the Federal Reserve's target. This affects my real return calculations.",
                "category": "economic_analysis"
            },
            {
                "text": "I want to set up a 529 plan for my child's education. What are the contribution limits and tax benefits?",
                "category": "education_planning"
            },
            {
                "text": "The stock market has been in a bear market for six months. Should I continue my regular investment contributions?",
                "category": "market_timing"
            },
            {
                "text": "I'm looking at a rental property with a cap rate of 8%. The cash flow analysis shows positive returns after expenses.",
                "category": "real_estate_investment"
            },
            {
                "text": "My employer offers a 401k match up to 6%. I'm currently contributing 4%. Should I increase my contribution?",
                "category": "retirement_optimization"
            },
            {
                "text": "The bond market is showing signs of stress. Should I reduce my bond allocation and increase cash or alternatives?",
                "category": "asset_allocation"
            }
        ]
        
        return conversations
    
    def create_synthetic_audio_dataset(self, num_samples: int = 1000) -> List[Dict]:
        """Create synthetic audio dataset with financial conversations."""
        dataset = []
        
        logger.info(f"Creating {num_samples} synthetic financial audio samples...")
        
        for i in tqdm(range(num_samples)):
            # Select random conversation
            conversation = np.random.choice(self.financial_conversations)
            
            # Add some variation to the text
            text = self._add_text_variation(conversation["text"])
            
            # Create synthetic audio (placeholder - in real implementation, use TTS)
            audio_path = self.output_dir / f"synthetic_audio_{i:04d}.wav"
            
            # Generate synthetic audio data (16kHz, mono)
            duration = len(text.split()) * 0.5  # Rough estimate: 0.5 seconds per word
            sample_rate = 16000
            samples = int(duration * sample_rate)
            
            # Create synthetic audio (white noise with some structure)
            audio_data = np.random.normal(0, 0.1, samples)
            # Add some structure to make it more realistic
            t = np.linspace(0, duration, samples)
            audio_data += 0.05 * np.sin(2 * np.pi * 440 * t)  # Add a tone
            
            # Save audio file
            sf.write(audio_path, audio_data, sample_rate)
            
            dataset.append({
                "audio": str(audio_path),
                "text": text,
                "category": conversation["category"],
                "duration": duration,
                "sample_rate": sample_rate
            })
        
        return dataset
    
    def _add_text_variation(self, text: str) -> str:
        """Add variations to text to increase dataset diversity."""
        variations = [
            # Add filler words
            lambda t: t.replace("I'm", "I am"),
            lambda t: t.replace("you're", "you are"),
            lambda t: t.replace("don't", "do not"),
            lambda t: t.replace("won't", "will not"),
            lambda t: t.replace("can't", "cannot"),
            
            # Add hesitations
            lambda t: t.replace("looking to", "looking to, um,"),
            lambda t: t.replace("considering", "considering, you know,"),
            lambda t: t.replace("thinking about", "thinking about, like,"),
            
            # Add emphasis
            lambda t: t.replace("significant", "very significant"),
            lambda t: t.replace("important", "really important"),
            lambda t: t.replace("good", "pretty good"),
        ]
        
        # Apply random variations
        for variation in np.random.choice(variations, size=np.random.randint(0, 3), replace=False):
            text = variation(text)
        
        return text
    
    def load_external_finance_datasets(self) -> List[Dict]:
        """Load external finance-specific datasets."""
        external_data = []
        
        # SEC Filing Audio (if available)
        sec_data = self._load_sec_filings()
        external_data.extend(sec_data)
        
        # Financial Podcast Data (if available)
        podcast_data = self._load_financial_podcasts()
        external_data.extend(podcast_data)
        
        # Earnings Call Data (if available)
        earnings_data = self._load_earnings_calls()
        external_data.extend(earnings_data)
        
        return external_data
    
    def _load_sec_filings(self) -> List[Dict]:
        """Load SEC filing audio data (placeholder implementation)."""
        # In a real implementation, you would:
        # 1. Download SEC filing audio from EDGAR
        # 2. Transcribe using existing Whisper model
        # 3. Clean and validate transcripts
        # 4. Extract financial terminology sections
        
        logger.info("Loading SEC filing data...")
        return []  # Placeholder
    
    def _load_financial_podcasts(self) -> List[Dict]:
        """Load financial podcast data (placeholder implementation)."""
        # In a real implementation, you would:
        # 1. Download financial podcasts (e.g., Motley Fool, Bloomberg)
        # 2. Segment into relevant financial discussions
        # 3. Transcribe and clean
        
        logger.info("Loading financial podcast data...")
        return []  # Placeholder
    
    def _load_earnings_calls(self) -> List[Dict]:
        """Load earnings call data (placeholder implementation)."""
        # In a real implementation, you would:
        # 1. Download earnings call audio from company websites
        # 2. Segment into relevant financial discussions
        # 3. Transcribe and clean
        
        logger.info("Loading earnings call data...")
        return []  # Placeholder
    
    def create_finance_terminology_dataset(self) -> List[Dict]:
        """Create dataset focused on financial terminology."""
        terminology_data = []
        
        # Create audio samples for each financial term
        for term in self.finance_terms:
            # Create variations of the term
            variations = [
                term,
                f"the {term}",
                f"this {term}",
                f"our {term}",
                f"your {term}",
                f"my {term}",
                f"a {term}",
                f"an {term}",
            ]
            
            for variation in variations:
                # Create synthetic audio for the term
                audio_path = self.output_dir / f"term_{term.replace(' ', '_')}_{len(terminology_data):04d}.wav"
                
                # Generate audio (shorter duration for single terms)
                duration = max(1.0, len(variation.split()) * 0.3)
                sample_rate = 16000
                samples = int(duration * sample_rate)
                
                audio_data = np.random.normal(0, 0.1, samples)
                t = np.linspace(0, duration, samples)
                audio_data += 0.05 * np.sin(2 * np.pi * 440 * t)
                
                sf.write(audio_path, audio_data, sample_rate)
                
                terminology_data.append({
                    "audio": str(audio_path),
                    "text": variation,
                    "category": "terminology",
                    "term": term,
                    "duration": duration,
                    "sample_rate": sample_rate
                })
        
        return terminology_data
    
    def process_and_clean_dataset(self, dataset: List[Dict]) -> List[Dict]:
        """Process and clean the dataset."""
        cleaned_dataset = []
        
        logger.info("Processing and cleaning dataset...")
        
        for item in tqdm(dataset):
            # Clean text
            text = self._clean_text(item["text"])
            
            # Validate audio file
            if self._validate_audio_file(item["audio"]):
                cleaned_dataset.append({
                    **item,
                    "text": text
                })
        
        return cleaned_dataset
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s.,!?;:\'"()-]', '', text)
        
        # Normalize case (keep proper nouns capitalized)
        text = text.lower()
        
        return text
    
    def _validate_audio_file(self, audio_path: str) -> bool:
        """Validate audio file exists and is readable."""
        try:
            if not os.path.exists(audio_path):
                return False
            
            # Try to load the audio file
            audio_data, sample_rate = librosa.load(audio_path, sr=16000)
            
            # Check if audio has reasonable duration
            duration = len(audio_data) / sample_rate
            if duration < 0.5 or duration > 30:
                return False
            
            return True
        except Exception as e:
            logger.warning(f"Failed to validate audio file {audio_path}: {e}")
            return False
    
    def save_dataset(self, dataset: List[Dict], filename: str = "finance_dataset.jsonl"):
        """Save dataset in JSONL format."""
        output_path = self.output_dir / filename
        
        logger.info(f"Saving dataset to {output_path}")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for item in dataset:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        
        logger.info(f"Saved {len(dataset)} samples to {output_path}")
    
    def create_huggingface_dataset(self, dataset: List[Dict]) -> Dataset:
        """Create Hugging Face dataset from the processed data."""
        logger.info("Creating Hugging Face dataset...")
        
        # Convert to Hugging Face format
        hf_dataset = Dataset.from_list(dataset)
        
        # Cast audio column to Audio feature
        hf_dataset = hf_dataset.cast_column("audio", Audio(sampling_rate=16000))
        
        return hf_dataset
    
    def generate_dataset_statistics(self, dataset: List[Dict]) -> Dict:
        """Generate statistics about the dataset."""
        stats = {
            "total_samples": len(dataset),
            "total_duration": sum(item.get("duration", 0) for item in dataset),
            "categories": {},
            "text_lengths": [],
            "durations": []
        }
        
        for item in dataset:
            # Category distribution
            category = item.get("category", "unknown")
            stats["categories"][category] = stats["categories"].get(category, 0) + 1
            
            # Text length distribution
            text_length = len(item.get("text", "").split())
            stats["text_lengths"].append(text_length)
            
            # Duration distribution
            duration = item.get("duration", 0)
            stats["durations"].append(duration)
        
        # Calculate statistics
        stats["avg_text_length"] = np.mean(stats["text_lengths"])
        stats["avg_duration"] = np.mean(stats["durations"])
        stats["total_hours"] = stats["total_duration"] / 3600
        
        return stats

def main():
    """Main function to prepare the finance dataset."""
    preparer = FinanceDatasetPreparer()
    
    logger.info("Starting finance dataset preparation...")
    
    # Create synthetic audio dataset
    synthetic_data = preparer.create_synthetic_audio_dataset(num_samples=1000)
    
    # Create terminology dataset
    terminology_data = preparer.create_finance_terminology_dataset()
    
    # Load external datasets (placeholder)
    external_data = preparer.load_external_finance_datasets()
    
    # Combine all datasets
    all_data = synthetic_data + terminology_data + external_data
    
    # Process and clean
    cleaned_data = preparer.process_and_clean_dataset(all_data)
    
    # Generate statistics
    stats = preparer.generate_dataset_statistics(cleaned_data)
    
    # Save dataset
    preparer.save_dataset(cleaned_data)
    
    # Create Hugging Face dataset
    hf_dataset = preparer.create_huggingface_dataset(cleaned_data)
    hf_dataset.save_to_disk(str(preparer.output_dir / "huggingface_dataset"))
    
    # Print statistics
    logger.info("Dataset Statistics:")
    logger.info(f"Total samples: {stats['total_samples']}")
    logger.info(f"Total duration: {stats['total_hours']:.2f} hours")
    logger.info(f"Average text length: {stats['avg_text_length']:.1f} words")
    logger.info(f"Average duration: {stats['avg_duration']:.2f} seconds")
    logger.info(f"Categories: {stats['categories']}")
    
    logger.info("Finance dataset preparation completed!")

if __name__ == "__main__":
    main()
