"""Command-line interface for the filing cabinet."""
import click
import os
from .services.file_service import FileService
from .config import get_config
from .cli_utils import (
    echo_error, echo_warning, echo_success, 
    echo_info, echo_header, format_error, 
    format_file_info, confirm_action, progress_spinner
)

DB_PATH = os.path.expanduser('~/filing.cabinet')
file_service = None
config_service = None

def init_services():
    """Initialize services."""
    global file_service, config_service
    if file_service is None:
        config_service = get_config(DB_PATH)
        file_service = FileService(DB_PATH)
    return file_service, config_service

@click.group()
def cli():
    """Filing cabinet CLI."""
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
        _, config = init_services()
        value = config.get(key, default)
        echo_info(f"{key}: {value}")
    except Exception as e:
        echo_error(format_error(e))
        exit(1)

@config.command(name="set")
@click.argument('key')
@click.argument('value')
def config_set(key, value):
    """Set a configuration value."""
    try:
        _, config = init_services()
        config.set(key, value)
        echo_success(f"Set {key} to {value}")
    except Exception as e:
        echo_error(format_error(e))
        exit(1)

@config.command(name="create")
@click.argument('key')
@click.argument('value')
@click.option('--default', help="Default value for the key")
@click.option('--description', help="Description of the configuration")
def config_create(key, value, default, description):
    """Create a new configuration entry."""
    try:
        _, config = init_services()
        config.create(key, value, default, description or '')
        echo_success(f"Created {key} with value {value}")
    except Exception as e:
        echo_error(format_error(e))
        exit(1)

@config.command(name="list")
def config_list():
    """List all configuration values."""
    try:
        _, config = init_services()
        configs = config.list_all()
        
        # Mask sensitive values
        if 'openai.api_key' in configs:
            key = configs['openai.api_key']['value']
            if key:
                configs['openai.api_key']['value'] = f"{key[:8]}...{key[-4:]}"
        
        for key, value in configs.items():
            echo_info(f"{key}:")
            echo_info(f"  Value: {value['value']}")
            if value['default']:
                echo_info(f"  Default: {value['default']}")
            if value['description']:
                echo_info(f"  Description: {value['description']}")
            echo_info()
    except Exception as e:
        echo_error(format_error(e))
        exit(1)

@config.command(name="reset")
@click.argument('key')
def config_reset(key):
    """Reset configuration value to default."""
    try:
        _, config = init_services()
        config.reset(key)
        echo_success(f"Reset {key} to default value")
    except Exception as e:
        echo_error(format_error(e))
        exit(1)

@config.command(name="export")
@click.argument('file_path')
def config_export(file_path):
    """Export configuration to a file."""
    try:
        _, config = init_services()
        config.export_to_file(file_path)
        echo_success(f"Configuration exported to {file_path}")
    except Exception as e:
        echo_error(format_error(e))
        exit(1)

@config.command(name="import")
@click.argument('file_path')
def config_import(file_path):
    """Import configuration from a file."""
    try:
        _, config = init_services()
        config.import_from_file(file_path)
        echo_success(f"Configuration imported from {file_path}")
    except Exception as e:
        echo_error(format_error(e))
        exit(1)

@config.command(name="set-openai-key")
@click.argument('api_key')
def config_set_openai_key(api_key):
    """Securely set the OpenAI API key in the configuration."""
    try:
        _, config = init_services()
        
        # Validate API key format (basic check)
        if not api_key.startswith(('sk-', 'org-')):
            echo_error("Error: Invalid OpenAI API key format. Key should start with 'sk-' or 'org-'")
            exit(1)
            
        try:
            # Try to get existing key first
            config.get('openai.api_key')
            # If key exists, update it
            config.set('openai.api_key', api_key)
            echo_success("OpenAI API key has been updated.")
        except Exception:
            # If key doesn't exist, create it
            config.create('openai.api_key', api_key, description='OpenAI API key for AI-powered document processing')
            echo_success("OpenAI API key has been securely stored in the configuration.")
        
        echo_info("Note: The key is stored in the database. Make sure to secure your database file.")
        
    except Exception as e:
        echo_error(format_error(e))
        exit(1)

@cli.command()
def status():
    """Show filing cabinet status."""
    try:
        service, _ = init_services()
        stats = service.get_statistics()
        
        echo_header("Filing Cabinet Status")
        echo_info(f"Total files: {stats['total_files']}")
        echo_info(f"Total size: {stats['total_size']} bytes")
        echo_info(f"Database location: {DB_PATH}")
        
    except Exception as e:
        echo_error(format_error(e))
        exit(1)

@cli.command()
@click.argument('path', type=click.Path(exists=True), default=os.path.expanduser('~'))
def index(path):
    """Index files in the given path."""
    try:
        service, _ = init_services()
        with progress_spinner("Indexing files"):
            result = service.index_files(path)
        if not result['processed']:
            echo_info("No new files found to index.")
        else:
            echo_success(f"Indexed {result['processed']} files")
            if result.get('skipped', 0) > 0:
                echo_warning(f"Skipped {result['skipped']} files")
    except Exception as e:
        echo_error(format_error(e))
        exit(1)

@cli.command()
@click.argument('path', type=click.Path(exists=True))
def process(path):
    """Process a file to extract metadata and content."""
    try:
        service, _ = init_services()
        with progress_spinner("Processing file"):
            service.process_file(path, extract_content=True)
        echo_success("File processed successfully")
    except Exception as e:
        echo_error(format_error(e))
        exit(1)

@cli.command()
@click.argument('checksum')
@click.argument('output_path', required=False)
def export(checksum, output_path):
    """Export a file from the filing cabinet to the filesystem."""
    try:
        service, _ = init_services()
        
        if output_path and os.path.exists(output_path):
            if not confirm_action(f"File {output_path} already exists. Overwrite?"):
                return
        
        with progress_spinner("Exporting file"):
            path = service.export_file(checksum, output_path)
        
        echo_success(f"File exported successfully to {path}")
        
    except Exception as e:
        echo_error(format_error(e))
        exit(1)

@cli.command()
@click.argument('path', type=click.Path(exists=True))
def analyze(path):
    """Analyze a file using AI to extract insights and metadata."""
    try:
        service, _ = init_services()
        with progress_spinner("Analyzing file"):
            result = service.analyze(path)
        
        echo_success("File analysis complete")
        echo_header("Analysis Results")
        
        # Display the basic file information
        echo_info("\nFile Information:")
        echo_info(f"Name: {result['name']}")
        echo_info(f"Size: {result['size']} bytes")
        echo_info(f"Type: {result['mime_type']}")
        echo_info(f"Checksum: {result['checksum']}")
                
    except Exception as e:
        echo_error(format_error(e))
        exit(1)

@cli.command()
@click.argument('path', type=click.Path(exists=True))
def add(path):
    """Add a file or directory to the filing cabinet."""
    try:
        service, _ = init_services()
        with progress_spinner("Processing files"):
            result = service.add_file(path)
        echo_success(f"Successfully processed {result['processed']} files")
        if result.get('skipped', 0) > 0:
            echo_warning(f"Skipped {result['skipped']} files")
    except Exception as e:
        echo_error(format_error(e))
        exit(1)

@cli.command()
@click.argument('query')
def search(query):
    """Search for files in the filing cabinet."""
    try:
        service, _ = init_services()
        results = service.search(query)
        
        if not results:
            echo_info("No matches found.")
            return
            
        echo_header(f"Search Results for '{query}'")
        for result in results:
            echo_info("\nFile:")
            echo_info(format_file_info(result))
            
    except Exception as e:
        echo_error(format_error(e))
        exit(1)

@cli.command()
@click.argument('file_id')
def info(file_id):
    """Get detailed information about a file."""
    try:
        service, _ = init_services()
        file_info = service.get_file_info(file_id)
        
        if not file_info:
            echo_error(f"No file found with ID: {file_id}")
            return
            
        echo_header("File Information")
        echo_info(format_file_info(file_info))
        
    except Exception as e:
        echo_error(format_error(e))
        exit(1)

@cli.command()
@click.argument('file_id')
def remove(file_id):
    """Remove a file from the filing cabinet."""
    try:
        service, _ = init_services()
        if confirm_action(f"Are you sure you want to remove file {file_id}?"):
            service.remove_file(file_id)
            echo_success(f"Successfully removed file {file_id}")
    except Exception as e:
        echo_error(format_error(e))
        exit(1)

if __name__ == '__main__':
    cli()