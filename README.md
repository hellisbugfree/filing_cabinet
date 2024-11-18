# Filing Cabinet

A command-line file management system that allows indexing, checking in, and checking out files.

it also supports post check-in processing such as OCR and metadata extraction, and pre check-out processing such as permission (?) and encryption (?).

the Idea is the database serves as a local repository of in some way or another important files to the user - may that be statement files, legal documents, invoices, or other work files which I want to store. this local repository can be copied (SQLite single file) to a remote location for backup or indeed for incorporation into a larger repository.

it allows for files to be auto or manually tagged with metadata such as date, source, author, Company, document type, etc.

based on the tags it may allow for automate keeping certain files in sync with multiple external folders/repositories. think tax advisor where I need to share documents of a given date range with specific tags, like #invoice #tax_advisor etc. 

## Installation

1. Clone this repository
2. Create a virtual environment: `python3 -m venv venv`
3. Activate the virtual environment: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Install the package: `pip install -e .`

## Usage

After installation, the following commands are available:

### File Management
- Index files: `filing index [PATH]`
- Check in a file: `filing checkin FILE_PATH`
- Get file info: `filing info FILE_PATH`
- Check out a file: `filing checkout CHECKSUM OUTPUT_PATH`

### Configuration Management
- List all settings: `filing config list`
- Get a setting: `filing config get KEY`
- Set a setting: `filing config set KEY VALUE`
- Create user setting: `filing config create user.KEY VALUE`

### Database Management
- Show database status: `filing status`

For more information, use `filing --help` or `filing COMMAND --help`

## Development Status

### V 0.0.1
- ✅ Basic file operations working
  - Check-in
  - Check-out
  - File info
- ⚠️ Index command needs refactoring (too broad in scope)

### V 0.1.1 
- ✅ Database status command
  - Shows DB path, name, version
  - Shows file and incarnation counts
  - Shows DB size and checksum
- ✅ Configuration management system
  - Database-backed configuration storage
  - Hierarchical naming convention (cabinet.*, database.*, file.*, user.*)
  - Default values for core settings
- ✅ File operation safety measures
  - Size limits for check-in
  - File type restrictions for indexing
  - Date range filtering for indexing

### Backlog

#### V 0.1.2 (Current)
- 🔄 Index command refactoring
  - Use file_incarnation table for tracking

#### V 0.1.3 (Planned)
- checkin 
  - the url is wrong only the short name - get the full name and device identifier like in the insert_file_incarnation
- refactor code to be more modular
- Database improvements
  - encapsulate schema management and versioning
- OCR processing and metadata extraction



#### Future Versions
index
  - Implement symlink detection and handling 


- 🔄 CLI improvements 
  - Add color output
  - Add logging
  - Add progress bars
  - Add error handling
  - Add help text  

- 🔄 File processing enhancements
  - Implement batch file processing limits
  - Add file type detection
  - Add basic metadata extraction

- introduce some prober database schema versioning and handl
- 📋 Google Sheets Integration
  - Export database contents to sheets
  - Import metadata from sheets
  - Real-time sync option
- 📋 Enhanced Metadata
  - OCR for PDFs and images
  - Automatic tag suggestions
  - Custom metadata fields
- 📋 External Storage
  - Cloud backup integration
  - Remote repository sync
  - Multi-device support
- 📋 UI/Visualization
  - Web interface for management
  - File relationship visualization
  - Tag cloud and statistics 
- 🔄 Configuration system improvements
  - Restrict config creation to valid prefixes only
  - Add config validation rules
  - Add config documentation command


### Quick Start for Development

1. Make your changes
2. Run `./scripts/commit.sh "Your commit message"` to commit and push changes
3. Run `./scripts/tag_version.sh X.Y.Z` to create a new version tag

### File Structure

- `filing_cabinet/` - Main package directory
  - [cli.py](cci:7://file:///Users/antonhell/Applications/filing_cabinet/filing_cabinet/cli.py:0:0-0:0) - Command-line interface and command implementations
  - `db.py` - Database operations and schema management
  - `config.py` - Configuration management system
- `scripts/` - Utility scripts for development
- `setup.py` - Package configuration
  - cabinet.path
  - cabinet.name - default is "filing Cabinet " + path 
  - cabinet.database.version - internal versioning for schema changes
  - file.checkin.max_size - for blob fields - default 5MB
  - file.checkin.max_files_at_once.warning - default 10
  - ...
- introduce get_config and put_config methods
  - get_config(key, default=None) - returns config value or default if not found
  - put_config(key, value) - sets config value
- make sure all commands deploy parameter safty measures i.e. 
    - checkin/out of more than filing.file.checkin.max_size, filing.file.checkin.max_files_at_once, ... 
    - index

what do I need for DB management? 
- at least a status command listing 
    - DB path
    - DB name
    - number file records
    - number file incarnations records
    - DB version
    - DB size
    - DB checksum
- a way to connect to google sheets? 
    - alternative solution to visually view/manage the db


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