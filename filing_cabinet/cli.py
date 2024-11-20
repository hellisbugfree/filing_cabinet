import click
import os
import hashlib
from datetime import datetime, timedelta
from .services.file_service import FileService
from .services.file_processor_service import FileProcessorService
from .config import ConfigService, ConfigurationError

DB_PATH = os.path.expanduser('~/filing.cabinet')
file_service = None
config_service = None
file_processor_service = None

def init_services():
    """Initialize services."""
    global file_service, config_service, file_processor_service
    if file_service is None or config_service is None or file_processor_service is None:
        config_service = ConfigService(DB_PATH)
        file_service = FileService(DB_PATH)
        file_processor_service = FileProcessorService(DB_PATH)
    return file_service, config_service, file_processor_service

@click.group()
def cli():
    """Filing Cabinet - A command-line file management system."""
    init_services()

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
        _, config, _ = init_services()
        value = config.get(key, default)
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
        _, config, _ = init_services()
        config.set(key, value)
        click.echo(f"Set {key} to {value}")
    except ConfigurationError as e:
        click.echo(str(e), err=True)
        exit(1)

@config.command(name="create")
@click.argument('key')
@click.argument('value')
@click.option('--default', help="Default value for the key")
@click.option('--description', help="Description of the configuration")
def config_create(key, value, default, description):
    """Create a new configuration entry."""
    try:
        _, config, _ = init_services()
        config.create(key, value, default, description or '')
        click.echo(f"Created {key} with value {value}")
    except ConfigurationError as e:
        click.echo(str(e), err=True)
        exit(1)

@config.command(name="list")
def config_list():
    """List all configuration values."""
    try:
        _, config, _ = init_services()
        config_dict = config.list_all()
        
        # Group by prefix
        groups = {}
        for key, data in config_dict.items():
            prefix = key.split('.')[0]
            if prefix not in groups:
                groups[prefix] = []
            groups[prefix].append((key, data))
        
        # Print grouped configuration
        for prefix, items in sorted(groups.items()):
            click.echo(f"\n[{prefix}]")
            for key, data in sorted(items):
                value = data.get('value', '')
                description = data.get('description', '')
                default = data.get('default_value', '')
                click.echo(f"{key} = {value}")
                if description:
                    click.echo(f"  # {description}")
                if default and default != value:
                    click.echo(f"  # Default: {default}")
    except ConfigurationError as e:
        click.echo(str(e), err=True)
        exit(1)

@config.command(name="reset")
@click.argument('key')
def config_reset(key):
    """Reset configuration value to default."""
    try:
        _, config, _ = init_services()
        config.reset(key)
        click.echo(f"Reset {key} to default value")
    except ConfigurationError as e:
        click.echo(str(e), err=True)
        exit(1)

@config.command(name="export")
@click.argument('file_path')
def config_export(file_path):
    """Export configuration to a file."""
    try:
        _, config, _ = init_services()
        config.export_to_file(file_path)
        click.echo(f"Configuration exported to {file_path}")
    except ConfigurationError as e:
        click.echo(str(e), err=True)
        exit(1)

@config.command(name="import")
@click.argument('file_path')
def config_import(file_path):
    """Import configuration from a file."""
    try:
        _, config, _ = init_services()
        config.import_from_file(file_path)
        click.echo(f"Configuration imported from {file_path}")
    except ConfigurationError as e:
        click.echo(str(e), err=True)
        exit(1)

@cli.command()
def status():
    """Show database status."""
    service, _, _ = init_services()
    stats = service.get_statistics()
    
    click.echo("Filing Cabinet Status:")
    click.echo(f"Name: {stats['name']}")
    click.echo(f"Version: {stats['version']}")
    click.echo(f"Total Files: {stats['total_files']}")
    click.echo(f"Total Incarnations: {stats['total_incarnations']}")

@cli.command()
@click.argument('path', type=click.Path(exists=True), default=os.path.expanduser('~'))
def index(path):
    """Index files in the given path."""
    service, _, _ = init_services()
    new_paths = service.index_files(path)
    
    if not new_paths:
        click.echo("No new file locations found.")
    else:
        for file_path in new_paths:
            click.echo(f"Indexed: {file_path}")

@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
def checkin(file_path):
    """Check in a file to the filing cabinet."""
    service, _, _ = init_services()
    try:
        checksum = service.checkin_file(file_path)
        click.echo(f"File checked in: {file_path} (Checksum: {checksum})")
    except ValueError as e:
        click.echo(f"Error: {str(e)}", err=True)
        exit(1)

@cli.command()
@click.argument('path', type=click.Path(exists=True))
def file_info(path):
    """Show detailed information about a file and all its incarnations."""
    service, _, _ = init_services()
    file, incarnations = service.get_file_info(path)
    
    if not file:
        click.echo(f"File not found in database: {path}")
        return
    
    click.echo("\nFile Information:")
    click.echo(f"Name: {file['name']}")
    click.echo(f"Checksum: {file['checksum']}")
    click.echo(f"Size: {file['size']} bytes")
    click.echo(f"Filed: {file['filed_time_stamp']}")
    click.echo(f"Last Update: {file['last_update_time_stamp']}")
    
    if incarnations:
        click.echo("\nIncarnations:")
        for inc in incarnations:
            click.echo(f"\n  Location: {inc['incarnation_url']}")
            click.echo(f"  Device: {inc['incarnation_device']}")
            click.echo(f"  Type: {inc['incarnation_type']}")
            if inc['forward_url']:
                click.echo(f"  Forward URL: {inc['forward_url']}")
            click.echo(f"  Last Update: {inc['last_update_time_stamp']}")

@cli.command()
@click.argument('checksum')
@click.argument('output_path', type=click.Path())
def checkout(checksum, output_path):
    """Check out a file from the filing cabinet."""
    service, _, _ = init_services()
    result = service.checkout_file(checksum, output_path)
    
    if result:
        click.echo(f"File checked out to: {result}")
    else:
        click.echo(f"File not found with checksum: {checksum}", err=True)

@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
def process_file(file_path):
    """Process a file to extract metadata and OCR content.
    
    Supports PDF files and common image formats (JPEG, PNG, TIFF).
    Extracts metadata and performs OCR, saving results to a .filing_meta_data file.
    """
    _, _, processor = init_services()
    metadata = processor.process_file(file_path)
    
    if metadata and processor.save_metadata(file_path, metadata):
        click.echo(f"Successfully processed {file_path}")
        click.echo(f"Metadata saved to {file_path}.filing_meta_data")
    else:
        click.echo(f"Failed to process {file_path}", err=True)
        exit(1)

if __name__ == '__main__':
    cli()