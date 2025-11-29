# 📦 Building and Publishing Terma AI Package

This guide explains how to build and publish the Terma AI package to PyPI.

## 🏗️ Building the Package

### 1. Install Build Tools

```bash
pip install build twine
```

### 2. Build Distribution Files

```bash
python -m build
```

This will create:
- `dist/terma-ai-3.0.0.tar.gz` (source distribution)
- `dist/terma_ai-3.0.0-py3-none-any.whl` (wheel distribution)

### 3. Verify Build

Check the contents of the distribution:

```bash
# Check source distribution
tar -tzf dist/terma-ai-3.0.0.tar.gz | head -20

# Check wheel contents
python -m zipfile -l dist/terma_ai-3.0.0-py3-none-any.whl
```

## 🧪 Test Installation Locally

Before publishing, test the installation locally:

```bash
# Install from local build
pip install dist/terma_ai-3.0.0-py3-none-any.whl

# Or install from source
pip install dist/terma-ai-3.0.0.tar.gz

# Test the CLI
termai --help
termai run "list files"
```

## 📤 Publishing to PyPI

### 1. Test on TestPyPI First (Recommended)

```bash
# Upload to TestPyPI
twine upload --repository testpypi dist/*

# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ terma-ai
```

### 2. Publish to PyPI

```bash
# Upload to PyPI
twine upload dist/*

# Users can now install with:
pip install terma-ai
```

## ✅ Post-Publication Verification

After publishing, verify the installation:

```bash
# Create a fresh virtual environment
python3 -m venv test_env
source test_env/bin/activate

# Install from PyPI
pip install terma-ai

# Test CLI
termai --help
termai run "list files in current directory"
termai shell
termai goal "backup my files"
```

## 🔄 Version Updates

To release a new version:

1. Update version in `termai/__init__.py`:
   ```python
   __version__ = "3.0.1"
   ```

2. Update version in `pyproject.toml`:
   ```toml
   version = "3.0.1"
   ```

3. Build and publish:
   ```bash
   python -m build
   twine upload dist/*
   ```

## 📝 Package Structure

The package structure is:
```
termai/
├── __init__.py          # Package metadata
├── __main__.py          # Module entry point (python -m termai)
├── cli.py               # CLI entry point (termai command)
├── settings.yaml        # Default configuration
└── core/                # Core modules
    ├── __init__.py
    ├── llm.py
    ├── safety.py
    ├── executor.py
    └── ...
```

## 🎯 CLI Entry Points

The package provides two ways to run:

1. **Direct command** (after pip install):
   ```bash
   termai run "list files"
   termai shell
   termai goal "backup files"
   ```

2. **Module execution** (still works):
   ```bash
   python -m termai run "list files"
   ```

Both use the same `termai.cli:cli` entry point defined in `pyproject.toml`.

