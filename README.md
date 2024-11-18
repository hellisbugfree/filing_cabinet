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

- Index files: `filing index [PATH]`
- Check in a file: `filing checkin FILE_PATH`
- Get file info: `filing info FILE_PATH`
- Check out a file: `filing checkout CHECKSUM OUTPUT_PATH`

For more information, use `filing --help` or `filing COMMAND --help`

## Development
V 0.0.1
- checkin, checkout, info works as expected
- index
  - far to encompasing in the moment - needs to be refactored

V 0.1.0
- refactor index - idea is to quickly determine which file has incarnations on the device, and which kind of incarnation i.e. file or symlin
  - do not checkin files - use the file_incarnation table to build the file_incarnation table
  - only index files of a certain type 
    - for the moment no default, an extension or list of extensions must be passed
    - default is pdf and images (png, jpg, jpeg)
  - only index files of a certain size - default is 5MB
  - only index files of a certain date range - default is today and today - 30 days
- introduce config file
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