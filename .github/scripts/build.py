# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

"""
Simple build script to export penance_hunter notebook to GitHub Pages.
"""

import subprocess
from pathlib import Path

def main():
    output_dir = Path("_site")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Export the notebook as a readonly app
    cmd = [
        "uvx", "marimo", "export", "html-wasm",
        "--sandbox",
        "--mode", "run",
        "penance_hunter.py",
        "-o", str(output_dir / "index.html")
    ]

    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

    # Create .nojekyll file
    (output_dir / ".nojekyll").touch()

    print(f"Build complete. Output in {output_dir}")

if __name__ == "__main__":
    main()
