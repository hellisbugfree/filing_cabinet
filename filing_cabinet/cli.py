import click
import os
import hashlib
from datetime import datetime, timedelta
from filing_cabinet.db import FilingCabinetDB
from filing_cabinet.config import get_config, ConfigurationError

DB_PATH = os.path.expanduser('~/filing.cabinet')


@click.group()
def cli():
    """Filing Cabinet - A command-line file management system."""
    pass

@cli.group()
def config():
    """Configuration management commands."""
    pass

@config.command(name="get")
@click.argument('key')
@click.option('--default', help="Default value if key doesn't exist")
def config_get(key, default):
    """Get a configuration value."""
    try:
        value = get_config().get_config(key, default)
        click.echo(f"{key}: {value}")
    except ConfigurationError as e:
        click.echo(str(e), err=True)
        exit(1)

@config.command(name="set")
@click.argument('key')
@click.argument('value')
def config_set(key, value):
    """Set a configuration value."""
    try:
        get_config().put_config(key, value)
        click.echo(f"Set {key} to {value}")
    except ConfigurationError as e:
        click.echo(str(e), err=True)
        exit(1)

@config.command(name="create")
@click.argument('key')
@click.argument('value')
@click.option('--default', help="Default value for the key")
def config_create(key, value, default):
    """Create a new configuration entry."""
    try:
        get_config().create_config(key, value, default or value)
        click.echo(f"Created {key} with value {value}")
    except ConfigurationError as e:
        click.echo(str(e), err=True)
        exit(1)

@config.command(name="list")
def config_list():
    """List all configuration values."""
    db = FilingCabinetDB(DB_PATH)
    db.connect()
    
    db.cursor.execute("SELECT key, value FROM config ORDER BY key")
    rows = db.cursor.fetchall()
    
    if not rows:
        click.echo("No configuration entries found")
        return
        
    # Group by prefix
    groups = {}
    for key, value in rows:
        prefix = key.split('.')[0]
        if prefix not in groups:
            groups[prefix] = []
        groups[prefix].append((key, value))
    
    # Print grouped configuration
    for prefix in sorted(groups.keys()):
        click.echo(f"\n[{prefix}]")
        for key, value in sorted(groups[prefix]):
            click.echo(f"{key}: {value}")
    
    db.close()

@cli.command()
def status():
    """Show database status."""
    db = FilingCabinetDB(DB_PATH)
    db.connect()
    db.create_tables()
    
    # Get database file path
    db_path = os.path.abspath(DB_PATH)
    
    # Calculate database size
    db_size = os.path.getsize(db_path)
    
    # Calculate database checksum
    with open(db_path, 'rb') as f:
        db_checksum = hashlib.sha256(f.read()).hexdigest()
    
    # Get record counts
    file_count = db.get_file_count()
    incarnation_count = db.get_incarnation_count()
    
    click.echo("Database Status:")
    click.echo(f"Path: {db_path}")
    click.echo(f"Name: {get_config().get_config('cabinet.name', 'Filing Cabinet')}")
    click.echo(f"Version: {get_config().get_config('database.schema.version')}")
    click.echo(f"Size: {db_size:,} bytes")
    click.echo(f"Checksum: {db_checksum}")
    click.echo(f"File Records: {file_count}")
    click.echo(f"File Incarnation Records: {incarnation_count}")
    
    db.close()

@cli.command()
@click.argument('path', type=click.Path(exists=True), default=os.path.expanduser('~'))
def index(path):
    """Index files in the given path."""
    db = FilingCabinetDB(DB_PATH)
    db.connect()
    db.create_tables()
    
    # Get configuration values - only care about extensions
    config = get_config()
    allowed_extensions = config.get_config('file.index.extensions')
    
    for root, _, files in os.walk(path):
        for file in files:
            file_path = os.path.join(root, file)
            if not os.path.isfile(file_path) and not os.path.islink(file_path):
                continue
                
            # Check file extension
            _, ext = os.path.splitext(file_path)
            if allowed_extensions and ext.lower() not in allowed_extensions:
                continue
            
            # Calculate checksum without inserting into file table
            checksum = db.get_file_checksum(file_path)
            
            # Add incarnation record
            abs_path = db.insert_file_incarnation(file_path, checksum)
            
            # Show different message based on whether file is in database
            if db.file_exists(checksum):
                click.echo(f"Found incarnation: {abs_path} (Checksum: {checksum})")
            else:
                click.echo(f"New file found: {abs_path} (Checksum: {checksum}). Use 'filing checkin' to add it to the cabinet.")
    
    db.close()

@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
def checkin(file_path):
    """Check in a file to the filing cabinet."""
    config = get_config()
    max_size = config.get_config('file.checkin.max_size')
    
    if os.path.getsize(file_path) > max_size:
        click.echo(f"Error: File size exceeds maximum allowed size of {max_size:,} bytes", err=True)
        exit(1)
        
    db = FilingCabinetDB(DB_PATH)
    db.connect()
    db.create_tables()

    checksum = db.insert_file(file_path)
    click.echo(f"File checked in: {file_path} (Checksum: {checksum})")

    db.close()

@cli.command()
@click.argument('path', type=click.Path(exists=True))
def file_info(path):
    """Show detailed information about a file and all its incarnations."""
    db = FilingCabinetDB(DB_PATH)
    db.connect()
    
    # First get file info
    result = db.get_file_info(path)
    if not result or not result[0]:
        click.echo(f"File not found in database: {path}")
        db.close()
        return
    
    file_info, incarnations = result
    checksum = file_info[0]  # First element is checksum
    
    click.echo(f"\nFile Information:")
    click.echo(f"Checksum: {checksum}")
    click.echo(f"URL: {file_info[1]}")
    click.echo(f"Filed: {file_info[2]}")
    click.echo(f"Last Updated: {file_info[3]}")
    click.echo(f"Name: {file_info[4]}")
    click.echo(f"Size: {file_info[5]} bytes")
    
    # Get all incarnations
    if not incarnations:
        click.echo("\nNo incarnations found.")
        db.close()
        return
    
    click.echo("\nIncarnations:")
    for inc in incarnations:
        click.echo("\n  Location:")
        click.echo(f"    Path: {inc[0]}")  # incarnation_url
        click.echo(f"    Device: {inc[1]}")  # incarnation_device
        click.echo("  Details:")
        click.echo(f"    Type: {inc[3]}")  # incarnation_type
        if inc[4]:  # forward_url for symlinks
            click.echo(f"    Forward URL: {inc[4]}")
        click.echo(f"    Last Updated: {inc[5]}")  # last_update_time_stamp
    
    db.close()

@cli.command()
@click.argument('checksum')
@click.argument('output_path', type=click.Path(exists=True))
def checkout(checksum, output_path):
    """Check out a file from the filing cabinet."""
    db = FilingCabinetDB(DB_PATH)
    db.connect()

    file_path = db.checkout_file(checksum, output_path)

    if file_path:
        click.echo(f"File checked out: {file_path}")
    else:
        click.echo("File not found in the filing cabinet.")

    db.close()

if __name__ == '__main__':
    cli()