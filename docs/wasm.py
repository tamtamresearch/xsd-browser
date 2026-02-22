from pathlib import Path

from main import render_html


def process_data(entry_path_str):
    """Process XSD from VFS path. JS already extracted ZIP to VFS."""
    return render_html(Path(entry_path_str), minify=False)
