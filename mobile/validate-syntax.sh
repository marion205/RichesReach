#!/bin/bash
# validate-syntax.sh — Hunt & fix missing commas in object literals

FILES=(src/shared/learningPaths.ts)  # Add more if needed: src/**/*.ts

for FILE in "${FILES[@]}"; do
  if [[ ! -f "$FILE" ]]; then
    echo "❌ $FILE missing."
    continue
  fi

  echo "🔍 Checking $FILE..."

  # Backup
  cp "$FILE" "$FILE.bak"
  echo "📦 Backup created: $FILE.bak"

  # Check current structure around potential issue area
  echo ""
  echo "Current structure (lines 995-1005):"
  sed -n '995,1005p' "$FILE" | cat -n

  # Try to validate with Node.js syntax check
  echo ""
  echo "🔍 Validating syntax..."
  if command -v node >/dev/null 2>&1; then
    node -e "
      const fs = require('fs');
      const content = fs.readFileSync('$FILE', 'utf8');
      // Basic syntax validation - check for balanced braces/brackets
      const lines = content.split('\\n');
      let braceCount = 0;
      let bracketCount = 0;
      let parenCount = 0;
      
      for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        braceCount += (line.match(/\{/g) || []).length - (line.match(/\}/g) || []).length;
        bracketCount += (line.match(/\[/g) || []).length - (line.match(/\]/g) || []).length;
        parenCount += (line.match(/\(/g) || []).length - (line.match(/\)/g) || []).length;
      }
      
      if (braceCount === 0 && bracketCount === 0 && parenCount === 0) {
        console.log('✅ Braces and brackets are balanced');
      } else {
        console.log('⚠️ Imbalance detected:');
        console.log('  Braces:', braceCount);
        console.log('  Brackets:', bracketCount);
        console.log('  Parentheses:', parenCount);
        process.exit(1);
      }
    " 2>&1
    
    if [ $? -eq 0 ]; then
      echo "✅ $FILE: Syntax appears valid"
    else
      echo "⚠️ $FILE: Syntax issues detected"
    fi
  else
    echo "⚠️ Node.js not available for validation"
  fi

  echo ""
done

# Bundle test suggestion
echo "🔄 To test bundling, run:"
echo "   npx expo start --clear"
echo ""
echo "If bundling fails, check the error and consider:"
echo "1. Reviewing lines 990-1010 for syntax issues"
echo "2. Running: mv src/shared/learningPaths.ts.bak src/shared/learningPaths.ts (to revert)"
echo "3. Using the simplified template if issues persist"

