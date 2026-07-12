# Suggested Commands Memory

Below are the developer commands commonly executed within this project on Windows environments.

## Virtual Environment Setup
```powershell
# Create virtual environment
python -m venv .venv

# Activate (PowerShell)
.\.venv\Scripts\Activate.ps1

# Install requirements
pip install -r requirements.txt
```

## Running the Web Application
```powershell
# Run the Flask App (defaults to port 5000)
python app.py
```

## Compilation of Styles (Tailwind CSS)
```powershell
# Watch and rebuild on utility changes
npm run dev:css

# Compile minified CSS for production
npm run build:css
```

## Running the Test Suite
```powershell
# Run all tests
pytest

# Run tests with stdout printing
pytest -s

# Run specific test file
pytest tests/test_sd_kyc_relation.py
```

## Packaging the Legacy Font Converter
```powershell
# Change directory
cd "DevLys Converter/devlys_converter_js"

# Install dependencies (pkg)
npm install

# Compile JS to Windows executable
npm run build:win
```
