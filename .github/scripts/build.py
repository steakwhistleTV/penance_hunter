# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

"""
Build script to export penance_hunter notebook to GitHub Pages.
Based on marimo-gh-pages-template structure.
"""

import subprocess
import shutil
from pathlib import Path

def main():
    output_dir = Path("_site")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Export the app (outputs to _site/apps/penance_hunter.html)
    notebook_path = Path("apps/penance_hunter_v2.py")
    output_file = output_dir / "apps" / "penance_hunter.html"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "uvx", "marimo", "export", "html-wasm",
        "--sandbox",
        "--mode", "run",
        "--no-show-code",
        str(notebook_path),
        "-o", str(output_file)
    ]

    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

    # Copy apps/public/ directory to _site/apps/public/ for assets (matching marimo template pattern)
    public_dir = Path("apps/public")
    if public_dir.exists():
        shutil.copytree(public_dir, output_dir / "apps" / "public", dirs_exist_ok=True)
        print(f"Copied apps/public/ to _site/apps/public/")

    # Create a redirect index.html at root to go to the app
    index_html = output_dir / "index.html"
    index_html.write_text('''<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="refresh" content="0; url=apps/penance_hunter.html">
</head>
<body>
    <p>Redirecting to <a href="apps/penance_hunter.html">Penance Hunter</a>...</p>
</body>
</html>
''')

    # Create .nojekyll file
    (output_dir / ".nojekyll").touch()

    print(f"Build complete. Output in {output_dir}")

if __name__ == "__main__":
    main()
