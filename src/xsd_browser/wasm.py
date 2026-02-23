from pathlib import Path

from main import render_html


def process_data(entry_path_str):
    """Process XSD from VFS path. JS already extracted ZIP to VFS."""
    try:
        html = render_html(Path(entry_path_str), minify=False)
        return {"ok": True, "html": html}
    except Exception as e:
        return {"ok": False, "error": str(e)}
