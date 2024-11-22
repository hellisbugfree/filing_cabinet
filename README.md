# Filing Cabinet

A command-line tool for managing and organizing your files with advanced processing capabilities.

## TODO
V
- 

## Features

- File indexing and organization
- Metadata extraction and content analysis
- Configurable file processing rules
- Search functionality
- AI-powered file analysis (coming soon)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/filing_cabinet.git
cd filing_cabinet
```

2. Create and activate a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Command Reference

### File Management

- `filing add <path>` - Add a file or directory to the cabinet
  - Processes and stores file metadata
  - Supports both single files and directories
  - Automatically skips ignored files (e.g., .git, __pycache__)

- `filing index <path>` - Index files in a directory
  - Scans directory for files without processing content
  - Creates a searchable index of file locations
  - Default path is user's home directory if not specified

- `filing process <path>` - Process a file to extract metadata and content
  - Extracts detailed metadata
  - Analyzes file content based on type
  - Stores extracted information for searching

- `filing export <checksum> [output_path]` - Export a file from the cabinet
  - Retrieves file by its checksum
  - Optionally specify output location
  - Preserves original file metadata

- `filing analyze <path>` - Analyze a file using AI
  - Extracts insights and summaries (requires OpenAI key)
  - Identifies topics and themes
  - Generates metadata suggestions

- `filing search <query>` - Search for files
  - Searches by filename, path, or content
  - Shows detailed file information
  - Orders results by relevance

- `filing info <file_id>` - Show detailed file information
  - Displays all metadata
  - Shows processing history
  - Lists extracted content info

- `filing remove <file_id>` - Remove a file from the cabinet
  - Removes file entry and metadata
  - Requires confirmation
  - Original file remains unchanged

- `filing status` - Show cabinet statistics
  - Total files and size
  - Processing statistics
  - Database location

### Configuration Management

- `filing config list` - List all configuration values
  - Shows current settings
  - Displays default values
  - Includes setting descriptions

- `filing config get <key>` - Get a configuration value
  - Retrieves specific setting
  - Shows current and default value
  - Supports optional default value

- `filing config set <key> <value>` - Set a configuration value
  - Updates setting
  - Validates value format
  - Preserves default value

- `filing config create <key> <value>` - Create a new configuration entry
  - Adds new setting
  - Supports default value
  - Allows description

- `filing config reset <key>` - Reset value to default
  - Restores default value
  - Preserves setting definition
  - Keeps description

- `filing config export <file_path>` - Export configuration
  - Saves all settings to file
  - Includes defaults and descriptions
  - Portable format

- `filing config import <file_path>` - Import configuration
  - Loads settings from file
  - Validates all values
  - Preserves existing settings not in file

- `filing config set-openai-key <api_key>` - Set OpenAI API key
  - Securely stores API key
  - Validates key format
  - Required for AI features

## Development

### Project Structure

```
filing_cabinet/
├── filing_cabinet/
│   ├── __init__.py
│   ├── cli.py              # Command-line interface
│   ├── cli_utils.py        # CLI utilities
│   ├── config.py           # Configuration management
│   ├── errors.py           # Custom exceptions
│   ├── models/             # Data models
│   ├── repositories/       # Database interactions
│   ├── services/          # Business logic
│   └── utils/             # Utility functions
├── tests/                 # Test suite
├── requirements.txt       # Dependencies
└── README.md             # Documentation
```

### Dependencies

Core dependencies:
- `click` - Command-line interface
- `python-magic` - File type detection

Optional dependencies for AI features:
- `openai` - AI-powered analysis

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.