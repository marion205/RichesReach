#!/bin/bash
# Clean RVM environment variables for this session

# Unset all RVM variables
unset GEM_PATH GEM_HOME RUBY_VERSION RUBY_ROOT MY_RUBY_HOME IRBRC
unset rvm_bin_path rvm_path rvm_prefix rvm_version
unset $(env | grep -o '^rvm_[^=]*' | xargs)

# Clean PATH of RVM entries
export PATH=$(echo $PATH | tr ':' '\n' | grep -v rvm | tr '\n' ':' | sed 's/:$//')

# Use system Ruby
export PATH="/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin:$PATH"

echo "✅ RVM environment cleaned"
echo "Ruby: $(which ruby) - $(ruby --version)"
echo "Pod: $(which pod) - $(pod --version 2>/dev/null || echo 'not found')"

