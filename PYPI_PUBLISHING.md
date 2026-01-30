# Publishing Updates to PyPI

When you make changes to the MCP servers, follow these steps to publish a new version.

## Step 1: Update Version Number

Edit `pyproject.toml` and increment the version:

```toml
version = "0.1.1"  # was 0.1.0
```

## Step 2: Rebuild Package

```powershell
cd hackathon-project

# Clean old builds
Remove-Item -Recurse -Force dist -ErrorAction SilentlyContinue

# Build new package
python -m build --sdist --wheel
```

## Step 3: Upload to PyPI

```powershell
# Create a new API token at https://pypi.org/manage/account/token/
twine upload dist/* -u __token__ -p YOUR_NEW_TOKEN
```

## Step 4: Verify

```powershell
# Force reinstall to get new version
pip install hackathon-sakhi --upgrade --force-reinstall

# Check version
pip show hackathon-sakhi
```

---

## Version History

| Version | Changes |
|---------|---------|
| 0.1.0 | Initial release - Weather, News, Telegram, Location servers |

---

## Quick Reference

```powershell
# Full publish workflow
$VERSION = "0.1.1"

# 1. Update version in pyproject.toml manually

# 2. Build
Remove-Item -Recurse -Force dist -ErrorAction SilentlyContinue
python -m build --sdist --wheel

# 3. Upload
twine upload dist/* -u __token__ -p $env:PYPI_TOKEN
```
