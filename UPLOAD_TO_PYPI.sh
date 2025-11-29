#!/bin/bash
# Script to upload termai package to PyPI

# Instructions:
# 1. Get your PyPI API token from: https://pypi.org/manage/account/token/
# 2. Set it as an environment variable or replace it below
# 3. Run this script: bash UPLOAD_TO_PYPI.sh

# Activate virtual environment
source venv/bin/activate

# Set PyPI credentials
# Option 1: Use environment variables (recommended)
# export TWINE_USERNAME=__token__
# export TWINE_PASSWORD=pypi-your-api-token-here

# Option 2: Uncomment and set your token directly (less secure)
# TWINE_USERNAME=__token__
# TWINE_PASSWORD=pypi-your-api-token-here

# Check if credentials are set
if [ -z "$TWINE_USERNAME" ] || [ -z "$TWINE_PASSWORD" ]; then
    echo "❌ Error: PyPI credentials not set!"
    echo ""
    echo "Please set your credentials:"
    echo "  export TWINE_USERNAME=__token__"
    echo "  export TWINE_PASSWORD=pypi-your-api-token-here"
    echo ""
    echo "Get your API token from: https://pypi.org/manage/account/token/"
    exit 1
fi

# Check if dist files exist
if [ ! -d "dist" ] || [ -z "$(ls -A dist/*.whl dist/*.tar.gz 2>/dev/null)" ]; then
    echo "❌ Error: No distribution files found in dist/"
    echo "Run: python3 -m build"
    exit 1
fi

# Upload to PyPI
echo "📦 Uploading termai package to PyPI..."
echo "Package version: $(ls dist/*.whl | sed 's/.*termai-\(.*\)-py3.*/\1/')"
echo ""

python -m twine upload dist/*

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Successfully uploaded to PyPI!"
    echo "📦 Package: termai"
    echo "🔗 View at: https://pypi.org/project/termai/"
    echo ""
    echo "Test installation with:"
    echo "  pip install termai"
else
    echo ""
    echo "❌ Upload failed. Check the error messages above."
    exit 1
fi

