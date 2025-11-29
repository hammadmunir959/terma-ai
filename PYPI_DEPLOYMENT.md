# PyPI Deployment Guide for Terma AI

This guide provides step-by-step instructions for deploying Terma AI to PyPI (Python Package Index).

## Prerequisites

Before deploying, ensure you have:

1. **PyPI Account**: Create an account at https://pypi.org/account/register/
2. **TestPyPI Account** (optional but recommended): Create an account at https://test.pypi.org/account/register/
3. **API Tokens**: Generate API tokens for both PyPI and TestPyPI
4. **Build Tools**: Install required build tools

## Step 1: Install Build Tools

```bash
# Install/upgrade build tools
pip install --upgrade build twine
```

## Step 2: Verify Package Configuration

### Check pyproject.toml

Ensure your `pyproject.toml` is properly configured:

- ✅ Package name: `terma-ai`
- ✅ Version: `3.0.0` (update for new releases)
- ✅ Description is clear and concise
- ✅ Author information is correct
- ✅ URLs point to your repository
- ✅ Dependencies are listed correctly
- ✅ Entry points (`termai` and `terma` commands) are defined

### Check MANIFEST.in

Verify that `MANIFEST.in` includes all necessary files:

```
include README.md
include LICENSE
include requirements.txt
recursive-include termai *.yaml
recursive-include termai *.yml
```

### Verify Package Structure

Ensure your package structure is correct:

```
terminal_ai/
├── pyproject.toml
├── README.md
├── LICENSE
├── MANIFEST.in
├── requirements.txt
└── termai/
    ├── __init__.py
    ├── cli.py
    ├── settings.yaml
    └── core/
        ├── __init__.py
        └── ... (all core modules)
```

## Step 3: Clean Previous Builds

```bash
# Remove old build artifacts
rm -rf build/
rm -rf dist/
rm -rf *.egg-info/
```

## Step 4: Build the Package

```bash
# Build source distribution and wheel
python -m build
```

This will create:
- `dist/terma-ai-3.0.0.tar.gz` (source distribution)
- `dist/terma_ai-3.0.0-py3-none-any.whl` (wheel)

## Step 5: Check the Package

### Verify Package Contents

```bash
# Check what files will be included
tar -tzf dist/terma-ai-3.0.0.tar.gz | head -20
```

### Test Installation Locally

```bash
# Install from local wheel to test
pip install dist/terma_ai-3.0.0-py3-none-any.whl

# Test the commands
termai --version
terma --version

# Uninstall after testing
pip uninstall terma-ai -y
```

## Step 6: Test on TestPyPI (Recommended)

Before deploying to production PyPI, test on TestPyPI:

### Upload to TestPyPI

```bash
# Upload to TestPyPI
python -m twine upload --repository testpypi dist/*

# You'll be prompted for:
# - Username: __token__
# - Password: Your TestPyPI API token (starts with pypi-)
```

### Test Installation from TestPyPI

```bash
# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ terma-ai

# Test the installation
termai --version
terma --version

# Uninstall after testing
pip uninstall terma-ai -y
```

## Step 7: Deploy to Production PyPI

Once tested on TestPyPI, deploy to production:

### Upload to PyPI

```bash
# Upload to production PyPI
python -m twine upload dist/*

# You'll be prompted for:
# - Username: __token__
# - Password: Your PyPI API token (starts with pypi-)
```

### Verify on PyPI

1. Visit https://pypi.org/project/terma-ai/
2. Verify package information is correct
3. Check that README renders properly
4. Verify installation instructions

## Step 8: Test Production Installation

```bash
# Install from PyPI
pip install terma-ai

# Verify installation
termai --version
terma --version
termai --help

# Test basic functionality
termai config
```

## Step 9: Update Version for Next Release

When preparing a new release:

1. **Update version in `pyproject.toml`**:
   ```toml
   version = "3.0.1"  # or next version
   ```

2. **Update version in `termai/__init__.py`**:
   ```python
   __version__ = "3.0.1"
   ```

3. **Update version badge in README.md**:
   ```markdown
   ![Version](https://img.shields.io/badge/version-3.0.1-blue)
   ```

4. **Commit and tag the release**:
   ```bash
   git add .
   git commit -m "Release version 3.0.1"
   git tag v3.0.1
   git push origin main --tags
   ```

## Troubleshooting

### Common Issues

#### 1. "Package already exists" Error

If you try to upload the same version twice:
- PyPI doesn't allow overwriting existing versions
- Increment the version number in `pyproject.toml` and `__init__.py`
- Rebuild and upload

#### 2. "Invalid package name" Error

- Ensure package name in `pyproject.toml` matches PyPI naming conventions
- Use lowercase letters, numbers, hyphens, and underscores only
- Current name: `terma-ai` ✅

#### 3. "Missing required files" Error

- Check `MANIFEST.in` includes all necessary files
- Verify `settings.yaml` is included
- Ensure `README.md` and `LICENSE` are in the root directory

#### 4. "Build failed" Error

- Ensure `pyproject.toml` is valid TOML
- Check that all dependencies are available
- Verify Python version compatibility

#### 5. "Authentication failed" Error

- Verify your API token is correct
- Ensure you're using `__token__` as username
- Check token has proper permissions (scope: entire account or project)

### Using API Tokens

1. **Generate Token**:
   - Go to https://pypi.org/manage/account/token/
   - Click "Add API token"
   - Give it a name (e.g., "terma-ai-deployment")
   - Set scope (entire account or specific project)
   - Copy the token (starts with `pypi-`)

2. **Use Token**:
   ```bash
   # Option 1: Enter when prompted
   python -m twine upload dist/*
   # Username: __token__
   # Password: pypi-xxxxxxxxxxxxx
   
   # Option 2: Use environment variable
   export TWINE_USERNAME=__token__
   export TWINE_PASSWORD=pypi-xxxxxxxxxxxxx
   python -m twine upload dist/*
   
   # Option 3: Use .pypirc (not recommended for tokens)
   # Store in ~/.pypirc (but tokens are safer)
   ```

## Quick Deployment Checklist

Before each deployment:

- [ ] Version number updated in `pyproject.toml`
- [ ] Version number updated in `termai/__init__.py`
- [ ] Version badge updated in `README.md`
- [ ] All tests pass: `pytest tests/`
- [ ] README is up to date
- [ ] LICENSE file is present
- [ ] `MANIFEST.in` includes all necessary files
- [ ] Cleaned old build artifacts
- [ ] Built new package: `python -m build`
- [ ] Tested local installation
- [ ] Tested on TestPyPI (optional but recommended)
- [ ] Ready to deploy to production PyPI

## Post-Deployment

After successful deployment:

1. **Verify Installation**:
   ```bash
   pip install terma-ai
   termai --version
   ```

2. **Update Documentation**:
   - Update any installation instructions
   - Update changelog if you maintain one

3. **Announce Release**:
   - Create GitHub release
   - Update release notes
   - Share on social media/forums if desired

## Version Numbering

Follow [Semantic Versioning](https://semver.org/):

- **MAJOR** (3.0.0): Breaking changes
- **MINOR** (3.1.0): New features, backward compatible
- **PATCH** (3.0.1): Bug fixes, backward compatible

Current version: **3.0.0**

## Security Notes

- **Never commit API tokens** to version control
- Use environment variables or secure credential storage
- Rotate tokens periodically
- Use project-scoped tokens when possible (instead of account-scoped)

## Additional Resources

- [PyPI Documentation](https://packaging.python.org/en/latest/guides/distributing-packages-using-setuptools/)
- [Twine Documentation](https://twine.readthedocs.io/)
- [Python Packaging Guide](https://packaging.python.org/)

---

**Last Updated**: 2024
**Package Name**: terma-ai
**Current Version**: 3.0.0

