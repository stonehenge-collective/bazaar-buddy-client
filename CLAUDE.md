# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build Commands
- Build executable: `cd client && pyinstaller --onefile main.py --add-data "tools\\tesseract;tesseract" --add-data "data;data"`
- Run application: `cd client && python main.py`
- Run text extractor tests: `cd client && python text_extractor.py`

## Code Style Guidelines
- Use Python type hints for all function parameters and return values
- Follow PEP 8 conventions for naming (snake_case for functions/variables, PascalCase for classes)
- Exception handling should use specific error types with detailed messages
- Use BLE001 noqa comments only when necessary for broad exception handling
- Organize classes with sections marked by comment headers (e.g., "public API", "internal helpers")
- Imports should be organized: standard library, third-party, local modules
- Signal/slot connections should use Qt.QueuedConnection for thread safety
- Use consistent indentation (4 spaces) and max line length of 100 characters
- Include docstrings for classes and public methods