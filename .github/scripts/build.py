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

    # Create root index with app cards
    index_html = output_dir / "index.html"
    index_html.write_text('''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Penance Hunter</title>
  <link href="https://fonts.googleapis.com/css2?family=UnifrakturCook:wght@700&display=swap" rel="stylesheet">
  <style>
    body {
      font-family: Arial, sans-serif;
      line-height: 1.6;
      color: #e0e0e0;
      background-color: #1a1a1a;
      padding: 20px;
      margin: 0;
    }
    .container {
      max-width: 800px;
      margin: 0 auto;
    }
    header {
      background-color: #2a2a2a;
      padding: 30px 20px;
      text-align: center;
      margin-bottom: 30px;
      border-bottom: 2px solid #8b0000;
    }
    h1 {
      font-family: 'UnifrakturCook', serif;
      font-size: 42px;
      margin-bottom: 10px;
      color: #c9a227;
    }
    .subtitle {
      font-size: 16px;
      color: #888;
      margin: 0 auto;
    }
    .section-title {
      font-size: 20px;
      margin: 20px 0 10px;
      text-align: center;
      color: #c9a227;
    }
    .cards {
      display: flex;
      flex-wrap: wrap;
      gap: 20px;
      margin: 20px 0;
      justify-content: center;
    }
    .card {
      background-color: #2a2a2a;
      border: 1px solid #444;
      flex: 1 0 300px;
      max-width: 350px;
    }
    .card-header {
      background-color: #3a3a3a;
      padding: 15px;
      font-weight: bold;
      font-size: 18px;
      color: #e0e0e0;
      border-bottom: 1px solid #444;
    }
    .card-body {
      padding: 20px;
    }
    .card-description {
      color: #888;
      margin-bottom: 15px;
      font-size: 14px;
    }
    .card-link {
      display: inline-block;
      background-color: #8b0000;
      color: white;
      padding: 10px 20px;
      text-decoration: none;
      font-weight: bold;
      transition: background-color 0.2s;
    }
    .card-link:hover {
      background-color: #a50000;
    }
    .card-link.beta {
      background-color: #c9a227;
      color: #1a1a1a;
    }
    .card-link.beta:hover {
      background-color: #ddb52f;
    }
    footer {
      background-color: #2a2a2a;
      text-align: center;
      padding: 20px 0;
      margin-top: 40px;
      border-top: 1px solid #444;
    }
    footer p {
      color: #666;
      font-size: 14px;
    }
    footer a {
      color: #c9a227;
      text-decoration: none;
    }
  </style>
</head>
<body>
  <header>
    <div class="container">
      <h1>Penance Hunter</h1>
      <p class="subtitle">Track your Darktide penance progress</p>
    </div>
  </header>

  <main class="container">
    <h2 class="section-title">Apps</h2>
    <div class="cards">
      <div class="card">
        <div class="card-header">Penance Hunter</div>
        <div class="card-body">
          <p class="card-description">Stable release - view and track your penance completion progress.</p>
          <a href="apps/penance_hunter.html" class="card-link">Open App</a>
        </div>
      </div>
      <div class="card">
        <div class="card-header">Penance Hunter (Beta)</div>
        <div class="card-body">
          <p class="card-description">Beta version with new features - sidebar, operatives stats, and class charts.</p>
          <a href="beta/penance_hunter.html" class="card-link beta">Open Beta</a>
        </div>
      </div>
    </div>
  </main>

  <footer>
    <div class="container">
      <p>Built with <a href="https://marimo.io" target="_blank">marimo</a></p>
    </div>
  </footer>
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
