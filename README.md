# Filing Cabinet

A command-line file management system that allows indexing, checking in, and checking out files.

## Installation

1. Clone this repository
2. Create a virtual environment: `python3 -m venv venv`
3. Activate the virtual environment: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Install the package: `pip install -e .`

## Usage

After installation, the following commands are available:

- Index files: `filing index [PATH]`
- Check in a file: `filing checkin FILE_PATH`
- Get file info: `filing info FILE_PATH`
- Check out a file: `filing checkout CHECKSUM OUTPUT_PATH`

For more information, use `filing --help` or `filing COMMAND --help`

## Development

### Quick Start

1. Make your changes
2. Run `./scripts/commit.sh "Your commit message"` to commit and push changes
3. Run `./scripts/tag_version.sh X.Y.Z` to create a new version tag

### File Structure

- `filing_cabinet/` - Main package directory
  - `cli.py` - Command-line interface
  - `db.py` - Database operations
- `scripts/` - Utility scripts for development
- `setup.py` - Package configuration