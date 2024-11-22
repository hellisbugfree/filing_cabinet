"""CLI utilities for the filing cabinet."""
import click
import sys
import time
import threading
from typing import Any, Dict
from contextlib import contextmanager

class Style:
    """Style constants for CLI output."""
    SUCCESS = 'green'
    ERROR = 'red'
    WARNING = 'yellow'
    INFO = 'blue'
    HEADER = 'cyan'

def echo_error(message: str, *args: Any) -> None:
    """Print an error message in red."""
    click.secho(f"Error: {message}", fg=Style.ERROR, err=True)
    for arg in args:
        if arg:
            click.secho(str(arg), fg=Style.ERROR, err=True)

def echo_warning(message: str) -> None:
    """Print a warning message in yellow."""
    click.secho(message, fg=Style.WARNING)

def echo_success(message: str) -> None:
    """Print a success message in green."""
    click.secho(message, fg=Style.SUCCESS)

def echo_info(message: str = "") -> None:
    """Print an info message."""
    click.echo(message)

def echo_header(message: str) -> None:
    """Print a header message in cyan."""
    click.secho(message, fg=Style.HEADER)
    click.secho("-" * len(message), fg=Style.HEADER)

def format_error(error: Exception) -> str:
    """Format an error message."""
    return f"[{error.__class__.__name__}] {str(error)}"

def format_file_info(metadata: Dict[str, Any]) -> str:
    """Format file information for display."""
    lines = []
    for key, value in metadata.items():
        if isinstance(value, dict):
            lines.append(f"\n{key}:")
            for k, v in value.items():
                lines.append(f"  {k}: {v}")
        else:
            lines.append(f"{key}: {value}")
    return "\n".join(lines)

@contextmanager
def progress_spinner(message: str = "Processing"):
    """Display a spinner while processing."""
    spinner_chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
    stop_spinner = False
    
    def spin():
        i = 0
        while not stop_spinner:
            sys.stdout.write(f"\r{message} {spinner_chars[i]} ")
            sys.stdout.flush()
            i = (i + 1) % len(spinner_chars)
            time.sleep(0.1)
        sys.stdout.write("\r" + " " * (len(message) + 2) + "\r")
        sys.stdout.flush()
    
    spinner_thread = threading.Thread(target=spin)
    spinner_thread.daemon = True
    spinner_thread.start()
    
    try:
        yield
    finally:
        stop_spinner = True
        spinner_thread.join()

def confirm_action(message: str = "Are you sure?") -> bool:
    """Ask for user confirmation."""
    return click.confirm(message)
