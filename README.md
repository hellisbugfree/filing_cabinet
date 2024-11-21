# Filing Cabinet

A document processing and filing system with advanced OCR capabilities, designed to extract and organize structured data from various document types.

## Features

- **Advanced OCR Processing**
  - Intelligent text extraction from both scanned and digital PDFs
  - Table detection and structured data extraction
  - Multi-language support with automatic language detection
  - Metadata extraction from various file types

- **File Management**
  - File check-in and check-out with checksum verification
  - Track multiple incarnations (copies) of the same file
  - Automatic file indexing with configurable extensions

- **Document Analysis**
  - Automatic entity extraction (dates, amounts, etc.)
  - Key-value pair detection
  - Table structure preservation
  - PDF metadata extraction

## Installation

1. Clone the repository:
```bash
git clone https://github.com/hellisbugfree/filing-cabinet.git
cd filing-cabinet
```

2. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install the package in development mode:
```bash
pip install -e .
```

## System Requirements

- Python 3.9 or higher
- Tesseract OCR (with language support as needed)
- Poppler (for PDF processing)

On macOS, install system dependencies with:
```bash
brew install tesseract
brew install poppler
```

## Usage

Process a file with OCR and metadata extraction:
```bash
filing process-file path/to/document.pdf
```

The processed file will generate a metadata file (`document.pdf.filing_meta_data`) containing:
```json
{
    "filing_cabinet": {
        "checksum": "sha256_hash",
        "processed_at": "ISO-8601 timestamp",
        "version": "0.3.1"
    },
    "device_data": {
        "created_at": "ISO-8601 timestamp",
        "modified_at": "ISO-8601 timestamp",
        "accessed_at": "ISO-8601 timestamp",
        "permissions": "unix-style permissions",
        "device_info": {
            "hostname": "device hostname",
            "platform": "Darwin/Linux/Windows",
            "platform_version": "OS version",
            "platform_machine": "architecture",
            "device_id": "unique device identifier"
        }
    },
    "content": {
        "text": "extracted text content",
        "tables": ["detected tables"],
        "key_value_pairs": {
            "key1": "value1",
            "key2": "value2"
        },
        "entities": {
            "dates": ["detected dates"],
            "amounts": ["detected amounts"]
        }
    }
}
```

## Development

### Project Structure
```
filing-cabinet/
├── filing_cabinet/          # Main package directory
│   ├── services/           # Core services
│   │   └── file_processor_service.py
│   ├── models/            # Data models
│   ├── repositories/      # Database interactions
│   ├── config/           # Configuration
│   ├── utils/            # Helpers
│   └── cli/             # CLI interface
├── tests/                # Test files
│   └── fixtures/        # Test documents
├── pyproject.toml        # Project configuration
└── deploy.sh            # Deployment script
```

### Version Control

The project uses semantic versioning (MAJOR.MINOR.PATCH):
- MAJOR: Incompatible API changes
- MINOR: New features (backwards compatible)
- PATCH: Bug fixes (backwards compatible)

Current version: 0.3.1

Version is managed in `pyproject.toml` and synchronized with git tags using `deploy.sh`.

### Release Process

To create a new release:
```bash
./deploy.sh
```

This will:
1. Update version in pyproject.toml
2. Create a git tag
3. Push changes and tags to remote

## Recent Changes

- Improved metadata extraction with device information
- Added version tracking in metadata output
- Reorganized project structure for better maintainability
- Enhanced documentation and examples
- Cleaned up redundant files and directories
- Centralized version management in pyproject.toml

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest`
5. Submit a pull request

## License

[MIT License](LICENSE)

## Contact

- Author: hellisbugfree
- Email: fyi_public@protonmail.com