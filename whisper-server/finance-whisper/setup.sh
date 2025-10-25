#!/bin/bash

# Finance-Specific Whisper Training Setup Script
# Sets up the environment for fine-tuning Whisper on financial data

set -e

echo "🚀 Setting up Finance-Specific Whisper Training Environment"
echo "=========================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python 3.8+ is available
check_python() {
    print_status "Checking Python version..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
        
        if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 8 ]; then
            print_success "Python $PYTHON_VERSION found"
            PYTHON_CMD="python3"
        else
            print_error "Python 3.8+ required, found $PYTHON_VERSION"
            exit 1
        fi
    else
        print_error "Python 3 not found"
        exit 1
    fi
}

# Check if pip is available
check_pip() {
    print_status "Checking pip..."
    
    if command -v pip3 &> /dev/null; then
        print_success "pip3 found"
        PIP_CMD="pip3"
    elif command -v pip &> /dev/null; then
        print_success "pip found"
        PIP_CMD="pip"
    else
        print_error "pip not found"
        exit 1
    fi
}

# Check if CUDA is available
check_cuda() {
    print_status "Checking CUDA availability..."
    
    if command -v nvidia-smi &> /dev/null; then
        print_success "CUDA available"
        CUDA_AVAILABLE=true
    else
        print_warning "CUDA not available, will use CPU"
        CUDA_AVAILABLE=false
    fi
}

# Create virtual environment
create_venv() {
    print_status "Creating virtual environment..."
    
    if [ ! -d "venv" ]; then
        $PYTHON_CMD -m venv venv
        print_success "Virtual environment created"
    else
        print_warning "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    print_success "Virtual environment activated"
}

# Install requirements
install_requirements() {
    print_status "Installing requirements..."
    
    # Upgrade pip
    $PIP_CMD install --upgrade pip
    
    # Install PyTorch (with CUDA if available)
    if [ "$CUDA_AVAILABLE" = true ]; then
        print_status "Installing PyTorch with CUDA support..."
        $PIP_CMD install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
    else
        print_status "Installing PyTorch for CPU..."
        $PIP_CMD install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
    fi
    
    # Install other requirements
    $PIP_CMD install -r requirements.txt
    
    print_success "Requirements installed"
}

# Setup Weights & Biases (optional)
setup_wandb() {
    print_status "Setting up Weights & Biases..."
    
    if command -v wandb &> /dev/null; then
        print_success "Wandb already installed"
    else
        print_warning "Wandb not found, installing..."
        $PIP_CMD install wandb
    fi
    
    # Check if user is logged in
    if wandb whoami &> /dev/null; then
        print_success "Wandb user logged in"
    else
        print_warning "Wandb user not logged in. Run 'wandb login' to enable logging"
    fi
}

# Clone whisper.cpp
setup_whisper_cpp() {
    print_status "Setting up whisper.cpp..."
    
    if [ ! -d "whisper.cpp" ]; then
        git clone https://github.com/ggerganov/whisper.cpp.git
        print_success "whisper.cpp cloned"
    else
        print_warning "whisper.cpp already exists"
    fi
    
    # Build whisper.cpp
    cd whisper.cpp
    make
    cd ..
    
    print_success "whisper.cpp built"
}

# Create directories
create_directories() {
    print_status "Creating directories..."
    
    mkdir -p finance_dataset
    mkdir -p whisper-finance-lora
    mkdir -p whisper-finance-export
    mkdir -p logs
    
    print_success "Directories created"
}

# Test installation
test_installation() {
    print_status "Testing installation..."
    
    # Test Python imports
    $PYTHON_CMD -c "
import torch
import transformers
import datasets
import peft
import jiwer
print('All imports successful')
print(f'PyTorch version: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'CUDA version: {torch.version.cuda}')
    print(f'GPU count: {torch.cuda.device_count()}')
"
    
    print_success "Installation test passed"
}

# Main setup function
main() {
    echo "Starting setup process..."
    
    # Check prerequisites
    check_python
    check_pip
    check_cuda
    
    # Setup environment
    create_venv
    install_requirements
    setup_wandb
    setup_whisper_cpp
    create_directories
    
    # Test installation
    test_installation
    
    echo ""
    echo "🎉 Setup completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Activate virtual environment: source venv/bin/activate"
    echo "2. Run training: python train_finance_whisper.py"
    echo "3. Or run individual steps:"
    echo "   - Dataset preparation: python train_finance_whisper.py --dataset-only"
    echo "   - Training: python train_finance_whisper.py --train-only"
    echo "   - Export: python train_finance_whisper.py --export-only"
    echo ""
    echo "Configuration:"
    echo "- Edit config.json to customize training parameters"
    echo "- Enable/disable wandb logging in config.json"
    echo "- Adjust LoRA parameters for different model sizes"
    echo ""
    echo "For help: python train_finance_whisper.py --help"
}

# Run main function
main "$@"
