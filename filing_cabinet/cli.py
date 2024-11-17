import click
import os
from filing_cabinet.db import FilingCabinetDB

DB_PATH = os.path.expanduser('~/filing.cabinet')

@click.group()
def cli():
    """Filing Cabinet - A command-line file management system."""
    pass

@cli.command()
@click.argument('path', type=click.Path(exists=True), default=os.path.expanduser('~'))
def index(path):
    """Index files in the given path."""
    db = FilingCabinetDB(DB_PATH)
    db.connect()
    db.create_tables()

    for root, _, files in os.walk(path):
        for file in files:
            file_path = os.path.join(root, file)
            if os.path.isfile(file_path):
                checksum = db.insert_file(file_path)
                click.echo(f"Indexed: {file_path} (Checksum: {checksum})")

    db.close()

@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
def checkin(file_path):
    """Check in a file to the filing cabinet."""
    db = FilingCabinetDB(DB_PATH)
    db.connect()
    db.create_tables()

    checksum = db.insert_file(file_path)
    click.echo(f"File checked in: {file_path} (Checksum: {checksum})")

    db.close()

@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
def info(file_path):
    """Get information about a file."""
    db = FilingCabinetDB(DB_PATH)
    db.connect()

    file_info, incarnations = db.get_file_info(file_path)

    if file_info:
        click.echo("File Information:")
        click.echo(f"Checksum: {file_info[0]}")
        click.echo(f"URL: {file_info[1]}")
        click.echo(f"Filed: {file_info[2]}")
        click.echo(f"Last Updated: {file_info[3]}")
        click.echo(f"Name: {file_info[4]}")
        click.echo(f"Size: {file_info[5]} bytes")

        if incarnations:
            click.echo("\nIncarnations:")
            for inc in incarnations:
                click.echo(f"  URL: {inc[2]}")
                click.echo(f"  Type: {inc[3]}")
                click.echo(f"  Forward URL: {inc[4]}")
                click.echo(f"  Status: {inc[5]}")
                click.echo(f"  Last Checked: {inc[6]}")
                click.echo("")
    else:
        click.echo("File not found in the filing cabinet.")

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