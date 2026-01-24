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
    * {
      box-sizing: border-box;
    }
    body {
      font-family: Arial, sans-serif;
      line-height: 1.6;
      color: #e0e0e0;
      margin: 0;
      padding: 0;
      min-height: 100vh;
      background: url('apps/public/penances_background.png') center center / cover no-repeat fixed;
    }
    body::before {
      content: '';
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.65);
      z-index: 0;
    }
    .page-wrapper {
      position: relative;
      z-index: 1;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }
    .container {
      max-width: 800px;
      margin: 0 auto;
      padding: 0 20px;
    }
    header {
      padding: 60px 20px 40px;
      text-align: center;
    }
    h1 {
      font-family: 'UnifrakturCook', serif;
      font-size: 56px;
      margin-bottom: 10px;
      color: #c9a227;
      text-shadow: 0 0 20px rgba(139, 0, 0, 0.8), 0 2px 4px rgba(0, 0, 0, 0.8);
    }
    .subtitle {
      font-size: 18px;
      color: #ccc;
      margin: 0 auto;
      text-shadow: 0 1px 3px rgba(0, 0, 0, 0.8);
    }
    main {
      flex: 1;
      padding: 20px;
    }
    .section-title {
      font-size: 22px;
      margin: 20px 0 20px;
      text-align: center;
      color: #c9a227;
      text-shadow: 0 1px 3px rgba(0, 0, 0, 0.8);
    }
    .cards {
      display: flex;
      flex-wrap: wrap;
      gap: 24px;
      margin: 20px 0;
      justify-content: center;
    }
    .card {
      background: rgba(20, 20, 20, 0.85);
      border: 1px solid rgba(139, 0, 0, 0.5);
      border-radius: 8px;
      flex: 1 0 300px;
      max-width: 350px;
      backdrop-filter: blur(10px);
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
      transition: transform 0.2s, box-shadow 0.2s;
    }
    .card:hover {
      transform: translateY(-4px);
      box-shadow: 0 8px 30px rgba(0, 0, 0, 0.7);
    }
    .card-header {
      background: rgba(139, 0, 0, 0.3);
      padding: 16px 20px;
      font-weight: bold;
      font-size: 20px;
      color: #e0e0e0;
      border-bottom: 1px solid rgba(139, 0, 0, 0.5);
      border-radius: 8px 8px 0 0;
    }
    .card-body {
      padding: 20px;
    }
    .card-description {
      color: #aaa;
      margin-bottom: 20px;
      font-size: 14px;
      line-height: 1.5;
    }
    .card-link {
      display: inline-block;
      background: linear-gradient(135deg, #8b0000 0%, #5c0000 100%);
      color: white;
      padding: 12px 24px;
      text-decoration: none;
      font-weight: bold;
      border-radius: 4px;
      transition: all 0.2s;
      box-shadow: 0 2px 8px rgba(139, 0, 0, 0.4);
    }
    .card-link:hover {
      background: linear-gradient(135deg, #a50000 0%, #6c0000 100%);
      box-shadow: 0 4px 12px rgba(139, 0, 0, 0.6);
    }
    .card-link.beta {
      background: linear-gradient(135deg, #c9a227 0%, #8b6914 100%);
      color: #1a1a1a;
      box-shadow: 0 2px 8px rgba(201, 162, 39, 0.4);
    }
    .card-link.beta:hover {
      background: linear-gradient(135deg, #ddb52f 0%, #a57a18 100%);
      box-shadow: 0 4px 12px rgba(201, 162, 39, 0.6);
    }
    footer {
      text-align: center;
      padding: 30px 20px;
      border-top: 1px solid rgba(139, 0, 0, 0.3);
      background: rgba(0, 0, 0, 0.3);
    }
    footer p {
      color: #888;
      font-size: 14px;
      margin: 0;
    }
    footer a {
      color: #c9a227;
      text-decoration: none;
    }
    footer a:hover {
      text-decoration: underline;
    }
  </style>
</head>
<body>
  <div class="page-wrapper">
    <header>
      <div class="container">
        <h1>Penance Hunter</h1>
        <p class="subtitle">Track your Darktide penance progress</p>
      </div>
    </header>

    <main class="container">
      <h2 class="section-title">Choose Version</h2>
      <div class="cards">
        <div class="card">
          <div class="card-header">Stable</div>
          <div class="card-body">
            <p class="card-description">Production release with tested features. View and track your penance completion progress.</p>
            <a href="apps/penance_hunter.html" class="card-link">Open Stable</a>
          </div>
        </div>
        <div class="card">
          <div class="card-header">Beta</div>
          <div class="card-body">
            <p class="card-description">Latest features in testing. May contain bugs but includes newest improvements.</p>
            <a href="beta/penance_hunter.html" class="card-link beta">Open Beta</a>
          </div>
        </div>
      </div>
    </main>

    <footer>
      <div class="container">
        <p>Built with <a href="https://marimo.io" target="_blank">marimo</a> | <a href="https://github.com/steakwhistleTV/penance_hunter" target="_blank">GitHub</a></p>
      </div>
    </footer>
  </div>
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
