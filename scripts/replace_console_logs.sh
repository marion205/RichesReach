#!/bin/bash
# Script to replace console.log/warn/debug/info with logger equivalents

cd /Users/marioncollins/RichesReach/mobile/src

# Find all TypeScript/TSX files with console statements
find . -type f \( -name "*.ts" -o -name "*.tsx" \) -exec grep -l "console\.\(log\|warn\|debug\|info\)" {} \; | while read file; do
  # Check if logger is already imported
  if ! grep -q "import.*logger" "$file"; then
    # Add logger import after React imports
    if grep -q "^import.*from 'react'" "$file"; then
      # Find the last import line and add logger import after it
      sed -i '' '/^import.*from '\''react'\''/a\
import logger from '\''../../utils/logger'\'';
' "$file" 2>/dev/null || sed -i '' '/^import.*from "react"/a\
import logger from "../../utils/logger";
' "$file" 2>/dev/null
    else
      # Add at the top if no React import
      sed -i '' '1a\
import logger from '\''../../utils/logger'\'';
' "$file" 2>/dev/null || sed -i '' '1a\
import logger from "../../utils/logger";
' "$file" 2>/dev/null
    fi
  fi
  
  # Replace console.log with logger.log
  sed -i '' 's/console\.log(/logger.log(/g' "$file" 2>/dev/null
  # Replace console.warn with logger.warn
  sed -i '' 's/console\.warn(/logger.warn(/g' "$file" 2>/dev/null
  # Replace console.debug with logger.debug
  sed -i '' 's/console\.debug(/logger.debug(/g' "$file" 2>/dev/null
  # Replace console.info with logger.info
  sed -i '' 's/console\.info(/logger.info(/g' "$file" 2>/dev/null
done

echo "✅ Replaced console statements with logger"

