#!/bin/bash
# Production Dependencies Installation Script
# Installs TensorFlow and other production-ready ML libraries

echo "🚀 Installing Production ML Dependencies..."
echo "=========================================="

# Check Python version
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
echo "✅ Python version: $python_version"

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 not found. Installing pip..."
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    python3 get-pip.py --user
    rm get-pip.py
fi

echo ""
echo "📦 Installing Core ML Dependencies..."

# Core ML and Deep Learning
echo "   Installing TensorFlow..."
pip3 install tensorflow>=2.13.0

echo "   Installing PyTorch (alternative to TensorFlow)..."
pip3 install torch torchvision torchaudio

echo "   Installing Scikit-learn..."
pip3 install scikit-learn>=1.3.0

echo "   Installing XGBoost and LightGBM..."
pip3 install xgboost>=1.7.0 lightgbm>=4.0.0

echo ""
echo "📊 Installing Data Science Libraries..."

# Data manipulation and analysis
pip3 install pandas>=2.0.0 numpy>=1.24.0 scipy>=1.10.0
pip3 install matplotlib>=3.7.0 seaborn>=0.13.2 plotly>=5.15.0

# Statistical analysis
pip3 install statsmodels>=0.14.0 scipy>=1.10.0

# Time series analysis
pip3 install prophet>=1.1.0 arch>=6.2.0

echo ""
echo "🌐 Installing API and Web Libraries..."

# API integration
pip3 install requests>=2.31.0 aiohttp>=3.8.0 httpx>=0.24.0
pip3 install websockets>=11.0.0

# Financial data APIs
pip3 install yfinance>=0.2.0 alpha-vantage>=2.3.1 finnhub-python>=2.4.0
pip3 install quandl>=3.7.0

echo ""
echo "🔧 Installing Production Tools..."

# Production and monitoring
pip3 install redis>=4.5.0 celery>=5.3.0
pip3 install prometheus-client>=0.17.0
pip3 install mlflow>=2.5.0 wandb>=0.15.0

# Testing and validation
pip3 install pytest>=7.4.0 pytest-django>=4.5.0
pip3 install hypothesis>=6.75.0

echo ""
echo "📈 Installing Technical Analysis Libraries..."

# Technical analysis
pip3 install ta>=0.10.0 pandas-ta>=0.3.14b0
pip3 install tulipy>=0.4.0

echo ""
echo "🔒 Installing Security and Performance Libraries..."

# Security and performance
pip3 install cryptography>=41.0.0 bcrypt>=4.0.0
pip3 install uvicorn>=0.23.0 gunicorn>=21.2.0

echo ""
echo "🧪 Testing Installations..."

# Test TensorFlow
echo "   Testing TensorFlow..."
python3 -c "import tensorflow as tf; print(f'✅ TensorFlow {tf.__version__} installed successfully')"

# Test PyTorch
echo "   Testing PyTorch..."
python3 -c "import torch; print(f'✅ PyTorch {torch.__version__} installed successfully')"

# Test Scikit-learn
echo "   Testing Scikit-learn..."
python3 -c "import sklearn; print(f'✅ Scikit-learn {sklearn.__version__} installed successfully')"

echo ""
echo "📋 Installation Summary:"
echo "========================="
pip3 list | grep -E "(tensorflow|torch|sklearn|pandas|numpy|yfinance|ta)" | head -10

echo ""
echo "🎯 Next Steps:"
echo "1. Test the ML services: python3 test_ml_services.py"
echo "2. Run advanced demo: python3 demo_advanced_ml.py"
echo "3. Configure API keys for market data"
echo "4. Set up monitoring and logging"

echo ""
echo "✅ Production ML Dependencies Installation Complete!"
