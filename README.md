# Filing Cabinet

A command-line file management system for organizing and tracking files across your system.

## todo


## Features

- File check-in and check-out with checksum verification
- Track multiple incarnations (copies) of the same file
- Automatic file indexing with configurable extensions
- Flexible configuration management with import/export capabilities
- SQLite-based storage for file metadata and configuration

## Project Structure

```
filing_cabinet/
├── models/           # Domain models
│   ├── file.py      # File entity and operations
│   └── incarnation.py # File incarnation tracking
├── repositories/     # Data access layer
│   ├── base.py      # Generic repository interface
│   ├── file_repository.py
│   └── incarnation_repository.py
├── services/        # Business logic layer
│   └── file_service.py
├── config/         # Configuration management
│   ├── configuration.py
│   └── config_service.py
└── cli.py         # Command-line interface
```

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/filing_cabinet.git
cd filing_cabinet

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package
pip install -e .
```

## Usage

### Basic Commands

```bash
# Show filing cabinet status
filing status

# Index files in a directory
filing index [PATH]

# Check in a file
filing checkin FILE_PATH

# Get file information
filing file-info FILE_PATH

# Check out a file
filing checkout CHECKSUM OUTPUT_PATH
```

### Configuration Management

```bash
# List all configuration
filing config list

# Get a configuration value
filing config get KEY

# Set a configuration value
filing config set KEY VALUE

# Export configuration
filing config export CONFIG_FILE

# Import configuration
filing config import CONFIG_FILE

# Reset configuration to default
filing config reset KEY
```

## Configuration Options

Default configuration values:

```python
{
    'cabinet.name': 'Filing Cabinet',
    'database.schema.version': '1.0.0',
    'file.index.extensions': ['.txt', '.pdf', '.doc', '.docx'],
    'file.checkin.max_size': 100 * 1024 * 1024,  # 100MB
    'storage.compression': 'none',
    'storage.encryption': 'none',
    'indexing.recursive': True,
    'indexing.follow_symlinks': False,
    'indexing.ignore_patterns': ['.git/*', '*.pyc', '__pycache__/*']
}
```

## Recent Improvements

- ✅ Complete codebase refactoring for better modularity
- ✅ Implemented proper domain models and repositories
- ✅ Added comprehensive configuration management system
- ✅ Improved error handling and type safety
- ✅ Enhanced database schema management
- ✅ deployment script to git for deployment
- ✅ Fixed: Duplicate incarnation handling during indexing
   - Issue: SQLite unique constraint error when indexing same directory multiple times
   - Fix: Added update logic for existing incarnations instead of insert-only


## Recent Changes
- Added comprehensive logging system
- Created initial test suite for FileService and ConfigService
- Added development tools and testing dependencies
- Improved error handling across services

## Testing Backlog/Errors
1. make logging persistent in the database with 
- database.log.maximum_entries = default: 10000
- database.log.retention.storage_path = default: /var/log/filing_cabinet
2. Known Issues:
   - [ ] Need to handle symlinks properly during indexing
   - [ ] Add proper error handling for file permission issues
   - [ ] Add validation for configuration values
   - [ ] Improve error messages for database connection issues

## Planned Features

- [ ] Compression and encryption support
- [ ] Advanced OCR processing and metadata extraction
- [ ] File version control
- [ ] Enhanced symlink detection and handling
- [ ] Comprehensive test suite
- [ ] Performance optimization for large file indexing

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.