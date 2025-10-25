# Finance-Specific Whisper Fine-Tuning

Complete implementation for fine-tuning OpenAI's Whisper model on financial terminology and conversations, optimized for the RichesReach wealth management app.

## 🎯 Overview

This implementation provides:
- **Domain-Specific Training**: Fine-tuned for financial terminology and conversations
- **Parameter-Efficient Fine-Tuning (PEFT)**: Uses LoRA to train only 0.1-1% of parameters
- **Optimized for Mobile**: Quantized models for self-hosted deployment
- **Production Ready**: Complete pipeline from dataset preparation to deployment

## 🚀 Quick Start

### 1. Setup Environment
```bash
# Run the setup script
./setup.sh

# Activate virtual environment
source venv/bin/activate
```

### 2. Run Complete Pipeline
```bash
# Train the complete model
python train_finance_whisper.py
```

### 3. Deploy Model
```bash
# The trained model will be available in whisper-finance-export/
cd whisper-finance-export/deployment
./deploy.sh audio.wav
```

## 📋 Features

### Dataset Preparation
- **Synthetic Financial Conversations**: Generated financial discussions and terminology
- **Terminology Focus**: Specialized dataset for financial terms
- **Audio Augmentation**: Noise and variation for robustness
- **Quality Validation**: Automatic audio and text validation

### LoRA Fine-Tuning
- **Efficient Training**: Only trains 0.1-1% of model parameters
- **Finance-Specific Weighting**: Higher weight for financial terminology
- **Custom Metrics**: Finance-specific WER and CER evaluation
- **Wandb Integration**: Real-time training monitoring

### Model Export
- **GGML Conversion**: Export to Whisper.cpp format
- **Quantization**: Reduce model size with minimal accuracy loss
- **Deployment Package**: Ready-to-use binaries and scripts
- **Performance Testing**: Automatic model validation

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Dataset Prep    │    │ LoRA Training   │    │ Model Export    │
│                 │    │                 │    │                 │
│ • Synthetic     │───▶│ • PEFT          │───▶│ • GGML          │
│ • Terminology   │    │ • Finance Wt    │    │ • Quantization  │
│ • Validation    │    │ • Custom Metrics│    │ • Deployment    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📊 Performance Expectations

### Accuracy Improvements
- **Generic Whisper**: ~15-20% WER on financial audio
- **Finance-Tuned**: <5% WER on financial audio
- **Financial Terms**: <3% WER on terminology
- **Processing Time**: <1 second for 30-second clips

### Model Sizes
- **Base Model**: ~80MB (whisper-tiny.en)
- **LoRA Adapter**: ~5MB
- **Quantized Model**: ~25MB (q4_0)
- **Memory Usage**: <100MB during inference

## 🔧 Configuration

### Training Parameters
```json
{
  "training": {
    "model_name": "openai/whisper-tiny.en",
    "lora_r": 16,
    "lora_alpha": 32,
    "learning_rate": 1e-4,
    "num_train_epochs": 3,
    "per_device_train_batch_size": 8
  }
}
```

### Dataset Configuration
```json
{
  "dataset": {
    "num_synthetic_samples": 1000,
    "include_terminology": true,
    "include_external": false
  }
}
```

### Export Configuration
```json
{
  "export": {
    "quantization_type": "q4_0",
    "create_package": true
  }
}
```

## 📚 Usage Examples

### Complete Training Pipeline
```bash
# Run everything
python train_finance_whisper.py

# With custom config
python train_finance_whisper.py --config custom_config.json
```

### Individual Steps
```bash
# Only prepare dataset
python train_finance_whisper.py --dataset-only

# Only train model
python train_finance_whisper.py --train-only

# Only export model
python train_finance_whisper.py --export-only --lora-model ./whisper-finance-lora
```

### Custom Training
```python
from fine_tune_whisper import FinanceWhisperTrainer, FinanceWhisperConfig

# Custom configuration
config = FinanceWhisperConfig(
    model_name="openai/whisper-small.en",
    lora_r=32,
    learning_rate=5e-5,
    num_train_epochs=5
)

# Train model
trainer = FinanceWhisperTrainer(config)
trainer.train()
```

## 🎯 Financial Terminology Coverage

### Investment Terms
- Portfolio, diversification, asset allocation
- Risk management, volatility, beta, alpha
- Sharpe ratio, return on investment
- Dividend yield, P/E ratio, market cap

### Trading Terms
- Bull/bear market, market correction
- Inflation, deflation, interest rates
- Federal Reserve, monetary policy
- Liquidity, leverage, margin, options

### Banking Terms
- Credit score, mortgage, refinancing
- Compound interest, APR, prime rate
- Treasury bonds, corporate bonds
- Yield curve, junk bonds

### Tax Terms
- Tax deduction, tax credit
- Capital gains, tax loss harvesting
- Roth IRA, traditional IRA, 401k
- Standard deduction, tax bracket

### Real Estate Terms
- Appreciation, depreciation, equity
- Lien, escrow, closing costs
- Down payment, PMI
- Home equity loan, cap rate

### Cryptocurrency Terms
- Bitcoin, Ethereum, blockchain
- DeFi, NFT, smart contract
- Mining, staking, wallet
- Exchange, cold storage

### Business Terms
- Revenue, profit margin, EBITDA
- Cash flow, balance sheet
- Income statement, audit
- Due diligence, merger, IPO

## 🔍 Evaluation Metrics

### Standard Metrics
- **WER (Word Error Rate)**: Overall transcription accuracy
- **CER (Character Error Rate)**: Character-level accuracy
- **BLEU Score**: Translation quality (if applicable)

### Finance-Specific Metrics
- **Finance WER**: Accuracy on financial terminology
- **Term Recognition**: Percentage of financial terms correctly transcribed
- **Context Accuracy**: Accuracy in financial conversation context

### Performance Metrics
- **Inference Speed**: Time per audio second
- **Memory Usage**: RAM consumption during inference
- **Model Size**: File size and memory footprint

## 🚀 Deployment

### Self-Hosted Deployment
```bash
# Copy deployment package to server
scp -r whisper-finance-export/deployment/ user@server:/opt/whisper-finance/

# Run on server
cd /opt/whisper-finance/
./deploy.sh audio.wav
```

### Integration with RichesReach
```javascript
// Update Whisper server to use finance-tuned model
const modelPath = path.join(__dirname, 'models/ggml-whisper-finance-q4_0.bin');

// In transcription endpoint
const command = `./main -m ${modelPath} -f ${wavPath} --language en --best-of 5`;
```

### Docker Deployment
```dockerfile
FROM node:18-alpine

# Copy whisper.cpp and model
COPY whisper.cpp/ /app/whisper.cpp/
COPY models/ggml-whisper-finance-q4_0.bin /app/models/

# Build whisper.cpp
RUN cd /app/whisper.cpp && make

# Copy server code
COPY server.js /app/
COPY package.json /app/

# Install dependencies
RUN cd /app && npm install

# Expose port
EXPOSE 3001

# Start server
CMD ["node", "/app/server.js"]
```

## 🧪 Testing

### Unit Tests
```bash
# Run tests
python -m pytest tests/

# With coverage
python -m pytest tests/ --cov=.
```

### Integration Tests
```bash
# Test complete pipeline
python test_pipeline.py

# Test model inference
python test_inference.py
```

### Performance Tests
```bash
# Benchmark inference speed
python benchmark.py

# Test accuracy on financial audio
python test_accuracy.py
```

## 📈 Monitoring

### Training Monitoring
- **Wandb Integration**: Real-time training metrics
- **TensorBoard**: Local training visualization
- **Custom Metrics**: Finance-specific evaluation

### Production Monitoring
- **Inference Speed**: Track processing time
- **Accuracy Metrics**: Monitor WER/CER over time
- **Error Logging**: Track transcription failures

## 🔧 Troubleshooting

### Common Issues

#### 1. CUDA Out of Memory
```bash
# Reduce batch size
"per_device_train_batch_size": 4

# Use gradient accumulation
"gradient_accumulation_steps": 2
```

#### 2. Training Too Slow
```bash
# Use smaller model
"model_name": "openai/whisper-tiny.en"

# Reduce LoRA rank
"lora_r": 8
```

#### 3. Poor Accuracy
```bash
# Increase training data
"num_synthetic_samples": 2000

# Adjust learning rate
"learning_rate": 5e-5
```

#### 4. Model Export Issues
```bash
# Check whisper.cpp installation
cd whisper.cpp && make

# Verify model files
ls -la whisper-finance-lora/
```

### Debug Commands
```bash
# Check GPU availability
python -c "import torch; print(torch.cuda.is_available())"

# Test dataset loading
python -c "from prepare_finance_dataset import *; print('Dataset OK')"

# Test model loading
python -c "from fine_tune_whisper import *; print('Model OK')"
```

## 📚 References

### Papers
- [LoRA: Low-Rank Adaptation of Large Language Models](https://arxiv.org/abs/2106.09685)
- [Whisper: Robust Speech Recognition via Large-Scale Weak Supervision](https://arxiv.org/abs/2212.04356)
- [Parameter-Efficient Fine-Tuning for Large Language Models](https://arxiv.org/abs/2203.02155)

### Documentation
- [Hugging Face Transformers](https://huggingface.co/docs/transformers/)
- [PEFT Library](https://huggingface.co/docs/peft/)
- [Whisper.cpp](https://github.com/ggerganov/whisper.cpp)

### Datasets
- [LibriSpeech](https://www.openslr.org/12/)
- [Common Voice](https://commonvoice.mozilla.org/)
- [Financial Audio Datasets](https://www.kaggle.com/datasets)

## 🤝 Contributing

### Adding New Financial Terms
1. Update `finance_terms` list in `prepare_finance_dataset.py`
2. Add corresponding audio samples
3. Retrain model with updated dataset

### Improving Training
1. Experiment with LoRA parameters
2. Add new evaluation metrics
3. Optimize training hyperparameters

### Enhancing Dataset
1. Add real financial audio data
2. Improve synthetic data generation
3. Add more diverse financial conversations

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- OpenAI for the Whisper model
- Hugging Face for the Transformers library
- Microsoft for the LoRA technique
- The open-source community for whisper.cpp

---

**Ready to improve your financial transcription accuracy? Start with `./setup.sh` and follow the quick start guide!** 🚀
