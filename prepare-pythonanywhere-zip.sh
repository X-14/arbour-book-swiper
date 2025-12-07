#!/bin/bash

# 📦 Prepare ZIP file for PythonAnywhere upload
# This script creates a clean ZIP file with only necessary files

echo "📦 Preparing Arbour Book Swiper for PythonAnywhere Upload"
echo "=========================================================="
echo ""

cd "/Users/xavierjudge/Desktop/Arbour Book Swiper/Anti Gravity Recomendation"

# Create output directory on Desktop for easy access
OUTPUT_DIR="/Users/xavierjudge/Desktop"
ZIP_NAME="arbour_book_swiper_pythonanywhere.zip"
OUTPUT_PATH="$OUTPUT_DIR/$ZIP_NAME"

echo "🗂️  Creating ZIP file..."
echo ""

# Remove old ZIP if exists
if [ -f "$OUTPUT_PATH" ]; then
    rm "$OUTPUT_PATH"
    echo "   Removed old ZIP file"
fi

# Create ZIP with only necessary files
zip -r "$OUTPUT_PATH" \
    app.py \
    firebase_dal.py \
    train_model.py \
    requirements.txt \
    serviceAccountKey.json \
    models/ \
    templates/ \
    static/ \
    -x "*.pyc" "*__pycache__*" "*.DS_Store" ".git*" \
       "venv/*" "sklearn-env/*" ".firebase/*" \
       "functions/*" "public/*" \
       "*.log" "*.pid"

# Check if successful
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ ZIP file created successfully!"
    echo ""
    echo "📍 Location: $OUTPUT_PATH"
    echo ""
    
    # Get ZIP file size
    ZIP_SIZE=$(du -h "$OUTPUT_PATH" | cut -f1)
    echo "📊 Size: $ZIP_SIZE"
    echo ""
    
    # List contents
    echo "📋 Contents:"
    unzip -l "$OUTPUT_PATH" | tail -n +4 | head -n -2 | awk '{print "   " $4}'
    echo ""
    
    echo "=========================================================="
    echo "🎯 Next Steps:"
    echo ""
    echo "1. Go to: https://www.pythonanywhere.com/registration/register/beginner/"
    echo "2. Create a free account"
    echo "3. Go to 'Files' tab"
    echo "4. Upload this ZIP file: $ZIP_NAME"
    echo "5. Extract it in the Files interface"
    echo "6. Follow PYTHONANYWHERE_DEPLOY_GUIDE.md for detailed steps"
    echo ""
    echo "The ZIP file is on your Desktop for easy access!"
    echo "=========================================================="
else
    echo ""
    echo "❌ Error creating ZIP file"
    echo "Please check that all files exist and try again"
fi

# Open Desktop folder to show the file
open "$OUTPUT_DIR"
