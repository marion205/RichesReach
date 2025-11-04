#!/bin/bash
# Wrapper script to run Expo iOS with proper CocoaPods environment
set -e

# Remove RVM from PATH completely
export PATH=$(echo "$PATH" | tr ':' '\n' | grep -v rvm | tr '\n' ':' | sed 's/:$//')
export PATH="/opt/homebrew/bin:/opt/homebrew/sbin:$PATH"

# Unset RVM variables
unset GEM_HOME
unset GEM_PATH
unset RUBYOPT
unset rvm_bin_path
unset rvm_path
unset rvm_prefix
unset rvm_version

# Set UTF-8 encoding (required by CocoaPods)
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

# Set architecture for glog build (fixes armv7 default)
export CURRENT_ARCH=arm64

# Navigate to mobile directory
cd "$(dirname "$0")" || exit 1

# Create a symlink to pod in PATH if it doesn't exist
POD_PATH="/opt/homebrew/Cellar/cocoapods/1.16.2_1/libexec/bin/pod"
if [ -f "$POD_PATH" ] && ! command -v pod >/dev/null 2>&1; then
    # Add the libexec bin to PATH
    export PATH="/opt/homebrew/Cellar/cocoapods/1.16.2_1/libexec/bin:$PATH"
fi

echo "Running Expo iOS with clean environment..."
echo "Using CocoaPods: $(which pod 2>/dev/null || echo 'Using direct path')"

# Run expo run:ios with all arguments passed through
npx expo run:ios "$@"

