#!/bin/bash
# Optimize Images for React Native
# Converts PNG/JPG to WebP format for better compression
# Usage: ./scripts/optimize-images.sh

set -e

ASSETS_DIR="./assets"
OUTPUT_DIR="./assets/optimized"
BACKUP_DIR="./assets/backup"

echo "🖼️  Optimizing Images..."
echo ""

# Check if imagemagick or cwebp is available
if ! command -v cwebp &> /dev/null; then
  echo "⚠️  cwebp not found. Installing..."
  echo ""
  echo "macOS: brew install webp"
  echo "Linux: sudo apt-get install webp"
  echo "Or use online converter: https://cloudconvert.com/png-to-webp"
  echo ""
  exit 1
fi

# Create directories
mkdir -p "${OUTPUT_DIR}"
mkdir -p "${BACKUP_DIR}"

# Find all images
find "${ASSETS_DIR}" -type f \( -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" \) | while read -r img; do
  filename=$(basename "$img")
  name="${filename%.*}"
  
  # Skip if already optimized
  if [[ "$filename" == *.webp ]]; then
    continue
  fi
  
  echo "Converting: ${filename}..."
  
  # Backup original
  cp "$img" "${BACKUP_DIR}/${filename}"
  
  # Convert to WebP (quality 85 - good balance)
  cwebp -q 85 "$img" -o "${OUTPUT_DIR}/${name}.webp"
  
  # Compare sizes
  original_size=$(stat -f%z "$img" 2>/dev/null || stat -c%s "$img" 2>/dev/null)
  webp_size=$(stat -f%z "${OUTPUT_DIR}/${name}.webp" 2>/dev/null || stat -c%s "${OUTPUT_DIR}/${name}.webp" 2>/dev/null)
  reduction=$(echo "scale=1; (1 - ${webp_size} / ${original_size}) * 100" | bc)
  
  echo "  ✅ ${filename} → ${name}.webp"
  echo "  📊 Size reduction: ${reduction}%"
  echo ""
done

echo "✅ Image optimization complete!"
echo "📁 Optimized images: ${OUTPUT_DIR}/"
echo "📁 Originals backed up: ${BACKUP_DIR}/"
echo ""
echo "⚠️  Note: Update imports in code to use .webp files"
echo "   Example: require('./assets/optimized/icon.webp')"

