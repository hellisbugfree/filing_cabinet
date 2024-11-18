import click
import os
import hashlib
from datetime import datetime, timedelta
from .services.file_service import FileService
from .config import initialize_config, get_config, ConfigurationError, ConfigService

DB_PATH = os.path.expanduser('~/filing.cabinet')

def init_services():
    """Initialize services."""
    # Create an instance of ConfigService with the DB path
    config_service = ConfigService(DB_PATH)
    
    # Initialize the service
    if not config_service.is_initialized:
        config_service.initialize(DB_PATH)
    
    return FileService(DB_PATH)

@click.group()
def cli():
    """Filing Cabinet - A command-line file management system."""
    pass

@cli.group()
def config():
    """Configuration management commands."""
    init_services()  # Initialize services for config commands
    pass

@config.command(name="get")
@click.argument('key')
@click.option('--default', help="Default value if key doesn't exist")
def config_get(key, default):
    """Get a configuration value."""
    try:
        value = get_config().get(key, default)
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
        get_config().set(key, value)
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
        get_config().create(key, value, default, description or '')
        click.echo(f"Created {key} with value {value}")
    except ConfigurationError as e:
        click.echo(str(e), err=True)
        exit(1)

@config.command(name="list")
def config_list():
    """List all configuration values."""
    try:
        config_dict = get_config().list_all()
        
        # Group by prefix
        groups = {}
        for key, data in config_dict.items():
            prefix = key.split('.')[0]
            if prefix not in groups:
                groups[prefix] = []
            groups[prefix].append((key, data))
        
        # Print grouped configuration
        for prefix in sorted(groups.keys()):
            click.echo(f"\n[{prefix}]")
            for key, data in sorted(groups[prefix]):
                value = data['value']
                default = data['default']
                description = data['description']
                
                click.echo(f"{key}: {value}")
                if description:
                    click.echo(f"  Description: {description}")
                if value != default:
                    click.echo(f"  Default: {default}")
    except ConfigurationError as e:
        click.echo(str(e), err=True)
        exit(1)

@config.command(name="reset")
@click.argument('key')
def config_reset(key):
    """Reset configuration value to default."""
    try:
        get_config().reset(key)
        click.echo(f"Reset {key} to default value")
    except ConfigurationError as e:
        click.echo(str(e), err=True)
        exit(1)

@config.command(name="export")
@click.argument('file_path')
def config_export(file_path):
    """Export configuration to a file."""
    try:
        get_config().export_to_file(file_path)
        click.echo(f"Configuration exported to {file_path}")
    except ConfigurationError as e:
        click.echo(str(e), err=True)
        exit(1)

@config.command(name="import")
@click.argument('file_path')
def config_import(file_path):
    """Import configuration from a file."""
    try:
        get_config().import_from_file(file_path)
        click.echo(f"Configuration imported from {file_path}")
    except ConfigurationError as e:
        click.echo(str(e), err=True)
        exit(1)

@cli.command()
def status():
    """Show database status."""
    service = init_services()
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
    service = init_services()
    new_paths = service.index_files(path)
    
    if not new_paths:
        click.echo("No new file locations found.")
    else:
        for file_path in new_paths:
            click.echo(f"Added new location: {file_path}")
        click.echo(f"\nAdded {len(new_paths)} new file location(s) to index.")

@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
def checkin(file_path):
    """Check in a file to the filing cabinet."""
    service = init_services()
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
    service = init_services()
    file, incarnations = service.get_file_info(path)
    
    if not file:
        click.echo(f"File not found in database: {path}")
        return
    
    click.echo(f"\nFile Information:")
    click.echo(f"Checksum: {file.checksum}")
    click.echo(f"Name: {file.name}")
    click.echo(f"Size: {file.size:,} bytes")
    click.echo(f"Filed: {file.filed_timestamp}")
    click.echo(f"Last Updated: {file.last_update_timestamp}")
    
    if incarnations:
        click.echo("\nIncarnations:")
        for inc in incarnations:
            click.echo(f"\n  Path: {inc.incarnation_url}")
            click.echo(f"  Device: {inc.incarnation_device}")
            click.echo(f"  Type: {inc.incarnation_type}")
            if inc.forward_url:
                click.echo(f"  Forward URL: {inc.forward_url}")
            click.echo(f"  Last Updated: {inc.last_update_timestamp}")

@cli.command()
@click.argument('checksum')
@click.argument('output_path', type=click.Path())
def checkout(checksum, output_path):
    """Check out a file from the filing cabinet."""
    service = init_services()
    result = service.checkout_file(checksum, output_path)
    
    if result:
        click.echo(f"File checked out to: {result}")
    else:
        click.echo(f"File not found with checksum: {checksum}", err=True)
        exit(1)

if __name__ == '__main__':
    cli()