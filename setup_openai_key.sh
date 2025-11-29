#!/bin/bash
# Quick script to set OpenAI API key for demo
# 
# Usage:
#   ./setup_openai_key.sh
#   Or: export OPENAI_API_KEY="your-key-here" && ./setup_openai_key.sh

if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  OPENAI_API_KEY environment variable not set"
    echo ""
    echo "To set it for this session:"
    echo "  export OPENAI_API_KEY=\"your-key-here\""
    echo ""
    echo "To make it permanent, add to your shell profile (.zshrc or .bashrc):"
    echo "  export OPENAI_API_KEY=\"your-key-here\""
    echo ""
    echo "Or create a .env.openai file:"
    echo "  echo 'your-key-here' > .env.openai"
    exit 1
fi

echo "✅ OpenAI API key set for this session"
echo "✅ Key length: ${#OPENAI_API_KEY} characters"
echo ""
echo "To make it permanent, add to your shell profile (.zshrc or .bashrc):"
echo "  export OPENAI_API_KEY=\"\$OPENAI_API_KEY\""
