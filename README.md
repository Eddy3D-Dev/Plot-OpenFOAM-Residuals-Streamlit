# Plot OpenFOAM Residuals

A modern single-page web app for visualizing OpenFOAM residual `.dat` and `.log` files, deployable directly on GitHub Pages.

## Features

- Interactive residual view (`Altair` tab equivalent)
- Static residual view (`Matplotlib` tab equivalent)
- Raw table inspection (`Dataframe` tab equivalent)
- Multi-file upload and side-by-side comparison
- Figure width/height controls for static plots
- Optional filename display
- Log-scale residual plotting
- Fully client-side parsing (files never leave the browser)

## Project Structure

- `web/index.html`: App shell
- `web/styles.css`: UI styling
- `web/app.js`: File parsing and plotting logic
- `.github/workflows/deploy-pages.yml`: GitHub Pages deployment workflow

## Local Preview

Serve the `web` directory with any static server.

```bash
python3 -m http.server 8000 --directory web
```

Then open `http://localhost:8000`.

## Deploy to GitHub Pages

1. Push to your default branch (workflow is configured for `main`).
2. In GitHub repo settings, enable Pages with source set to GitHub Actions.
3. The workflow in `.github/workflows/deploy-pages.yml` will publish the `web/` folder.

## How to Use

1. Upload one or more OpenFOAM residual `.dat` or `.log` files.
2. Configure static figure width/height and optionally enable filename labels.
3. Switch between `Altair`, `Matplotlib`, and `Dataframe` tabs.
