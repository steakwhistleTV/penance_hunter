# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

"""
Build script to export penance_hunter notebooks to GitHub Pages.
Builds both stable and beta versions from main branch.

URLs:
- steakwhistletv.github.io/penance_hunter/ -> stable (penance_hunter.py)
- steakwhistletv.github.io/penance_hunter/beta/ -> beta (penance_hunter_v2.py)
"""

import subprocess
import shutil
from pathlib import Path

def export_notebook(notebook_path: Path, output_file: Path):
    """Export a marimo notebook to HTML-WASM."""
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

def main():
    output_dir = Path("_site")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Build stable version (penance_hunter.py)
    print("=== Building stable version ===")
    stable_notebook = Path("apps/penance_hunter.py")
    stable_output = output_dir / "apps" / "penance_hunter.html"
    export_notebook(stable_notebook, stable_output)

    # Build beta version (penance_hunter_beta.py)
    print("=== Building beta version ===")
    beta_notebook = Path("apps/penance_hunter_beta.py")
    beta_output = output_dir / "beta" / "penance_hunter.html"
    export_notebook(beta_notebook, beta_output)

    # Copy public assets to both locations
    public_dir = Path("apps/public")
    if public_dir.exists():
        shutil.copytree(public_dir, output_dir / "apps" / "public", dirs_exist_ok=True)
        shutil.copytree(public_dir, output_dir / "beta" / "public", dirs_exist_ok=True)
        print(f"Copied apps/public/ to _site/apps/public/ and _site/beta/public/")

    # Create root index redirect to stable
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

    # Create beta index redirect
    beta_index = output_dir / "beta" / "index.html"
    beta_index.parent.mkdir(parents=True, exist_ok=True)
    beta_index.write_text('''<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="refresh" content="0; url=penance_hunter.html">
</head>
<body>
    <p>Redirecting to <a href="penance_hunter.html">Penance Hunter Beta</a>...</p>
</body>
</html>
''')

    # Create .nojekyll file
    (output_dir / ".nojekyll").touch()

    print(f"Build complete. Output in {output_dir}")
    print(f"  Stable: /apps/penance_hunter.html")
    print(f"  Beta:   /beta/penance_hunter.html")

if __name__ == "__main__":
    main()
