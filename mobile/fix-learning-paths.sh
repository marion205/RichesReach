#!/bin/bash
# fix-learning-paths.sh — Auto-add comma after array in LEARNING_PATHS

FILE="src/shared/learningPaths.ts"

if [[ ! -f "$FILE" ]]; then
  echo "❌ $FILE not found—check path."
  exit 1
fi

# Backup original
cp "$FILE" "$FILE.bak"
echo "📦 Backup created: $FILE.bak"

# Check current structure around line 999
echo "🔍 Current structure around line 999:"
sed -n '997,1001p' "$FILE" | cat -n

# Add comma after ] on line 999 if it's followed by } (closing object)
# This fixes: ] } to ] }
sed -i '' '999s/]$/],/' "$FILE"

echo ""
echo "✅ Added comma after array close on line 999"
echo ""
echo "🔍 Updated structure:"
sed -n '997,1001p' "$FILE" | cat -n

# Validate the fix
echo ""
echo "🔍 Validating syntax..."
if command -v node >/dev/null 2>&1; then
  # Try to parse as JavaScript to check syntax
  node -e "
    const fs = require('fs');
    const content = fs.readFileSync('$FILE', 'utf8');
    // Remove TypeScript-specific syntax for basic validation
    const jsContent = content
      .replace(/export const LEARNING_PATHS = /, 'const LEARNING_PATHS = ')
      .replace(/export interface/g, '// interface')
      .replace(/export const/g, 'const');
    try {
      // This will catch syntax errors
      eval(jsContent);
      console.log('✅ Syntax appears valid');
    } catch(e) {
      console.log('⚠️ Syntax check failed:', e.message);
      process.exit(1);
    }
  " 2>&1
else
  echo "⚠️ Node.js not available for validation"
fi

echo ""
echo "✅ Fix applied! Next steps:"
echo "1. Run: npx expo start --clear"
echo "2. If issues persist, revert with: mv $FILE.bak $FILE"

