# Plot OpenFOAM Residuals

A Streamlit app for visualizing OpenFOAM residual `.dat` and `.log` files.

## Features

- Interactive residual view (`Interactive` tab)
- Static residual view (`Static` tab) with Matplotlib
- Raw table inspection (`Data` tab)
- Multi-file upload and side-by-side comparison
- Height controls for interactive and static plots
- Optional filename display
- Log-scale residual plotting
- CSV download per uploaded file
- Server-side parsing in Streamlit

## Project Structure

- `streamlit_app.py`: Main Streamlit application
- `pyproject.toml`: Project metadata and dependencies
- `uv.lock`: Locked dependency set for `uv`

## Run Locally

Install dependencies with `uv` and run Streamlit:

```bash
uv sync
uv run streamlit run streamlit_app.py
```

Then open the local URL printed by Streamlit (usually `http://localhost:8501`).

## Deploy to Streamlit Cloud

1. Connect this repository in Streamlit Cloud.
2. Set main file path to `streamlit_app.py`.
3. Streamlit Cloud will install dependencies from `pyproject.toml`/`uv.lock`.

## How to Use

1. Upload one or more OpenFOAM residual `.dat` or `.log` files.
2. Configure optional display and plotting controls.
3. Switch between `Interactive`, `Static`, and `Data` tabs.
