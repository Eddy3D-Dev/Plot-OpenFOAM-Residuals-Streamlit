import io
import math
import tempfile
from pathlib import Path

import altair as alt
import matplotlib.pyplot as plt
import numpy as np
import openfoam_residuals.filesystem as fs
import openfoam_residuals.plot as orp
import pandas as pd
import streamlit as st

# Page configuration
st.set_page_config(
    page_title="OpenFOAM Residuals",
    page_icon="📈",
    layout="centered"
)


def create_altair_plot(data: pd.DataFrame) -> alt.Chart:
    """
    Create an Altair visualization for the residuals.

    Args:
        data (pd.DataFrame): The dataframe containing residual data.

    Returns:
        alt.Chart: The Altair chart object.
    """
    # reset_index() will create a 'Time' column from the index
    data_reset = data.reset_index()

    # ⚡ Bolt Optimization: Use Altair's transform_fold instead of pandas.melt()
    # Expected Performance Impact:
    # 1. Eliminates O(N) DataFrame melting on the backend, saving CPU time.
    # 2. Reduces backend memory footprint and the JSON payload size sent to the frontend by ~6x
    #    because we send the wide DataFrame instead of a 6x longer melted DataFrame.
    chart = alt.Chart(data_reset).transform_fold(
        ['Ux', 'Uy', 'Uz', 'p', 'epsilon', 'k'],
        as_=['Residual', 'Value']
    ).mark_line(point=False).encode(
        x=alt.X('Time:Q', title='Iteration'),  # Use the 'Time' column for the x-axis
        y=alt.Y('Value:Q', scale=alt.Scale(type='log'), title='Residuals'),
        color=alt.Color('Residual:N', title='Variable'),
        tooltip=[alt.Tooltip('Time:Q', title='Iteration'), alt.Tooltip('Residual:N', title='Variable'), alt.Tooltip('Value:Q', title='Residual', format='.2e')]  # Update tooltip to use 'Time'
    ).properties(
        width=800,
        height=400
    ).interactive()

    return chart


# ⚡ Bolt Optimization: Cache Matplotlib rendering using an image buffer and bypass DataFrame hashing.
# Expected Performance Impact:
# Generating Matplotlib figures and rendering them blocks the main thread on every app rerun.
# By caching the resulting PNG bytes, we bypass the O(N) plotting time and serialization overhead.
# We use `_data` to bypass Streamlit's expensive DataFrame hashing, and instead use `file_id`
# to invalidate the cache when a new file is uploaded.
@st.cache_data
def get_matplotlib_image_bytes(
    _data: pd.DataFrame,
    file_id: str,
    width: int,
    height: int,
    dpi: int
) -> bytes:
    # ⚡ Bolt Optimization: Compute min/max inside the cached function
    # Expected Performance Impact: By moving these calculations inside the cache hit boundary,
    # we eliminate the CPU overhead of computing them on every single Streamlit script rerun
    # (e.g., when the user toggles the sidebar checkbox).
    global_min = float(np.nanmin(_data.values))
    min_residual = math.pow(10, orp.order_of_magnitude(global_min))
    max_iter = int(_data.index[-1])  # OpenFOAM iterations are monotonically increasing

    fig = create_matplotlib_plot(_data, width, height, dpi, min_residual, max_iter)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


def create_matplotlib_plot(
    data: pd.DataFrame,
    width: int,
    height: int,
    dpi: int,
    min_residual: float,
    max_iter: int
) -> plt.Figure:
    """
    Create a Matplotlib visualization for the residuals.

    Args:
        data (pd.DataFrame): The dataframe containing residual data.
        width (int): The width of the figure.
        height (int): The height of the figure.
        dpi (int): The DPI (resolution) of the figure.
        min_residual (float): The minimum residual value for the y-axis.
        max_iter (int): The maximum iteration number for the x-axis.

    Returns:
        plt.Figure: The Matplotlib figure object.
    """
    plt.rcParams['figure.figsize'] = [width, height]
    # ⚡ Bolt Optimization: Use configurable DPI instead of hardcoded 600
    # Expected Performance Impact: Reduces Matplotlib rendering time by ~5-10x
    # and significantly decreases memory footprint and payload size.
    plt.rcParams['figure.dpi'] = dpi

    plot = data.plot(logy=True)
    fig = plot.get_figure()
    ax = plt.gca()
    ax.legend(loc='upper right')
    ax.set_xlabel("Iterations")
    ax.set_ylabel("Residuals")
    ax.set_ylim(min_residual, 1)
    ax.set_xlim(0, max_iter)

    return fig


@st.cache_data
def parse_uploaded_file(file_name: str, file_id: str, _file_content: bytes) -> pd.DataFrame:
    """
    Parse the uploaded file once and cache the result.
    This avoids redundant I/O and CPU overhead when switching between tabs.

    ⚡ Bolt Optimization: By adding a leading underscore to `_file_content`,
    we prevent Streamlit from hashing the large bytes payload on every rerun.
    Instead, Streamlit uses the small `file_id` string to manage cache invalidation.
    Expected Performance Impact: Eliminates multi-second UI blocking caused by hashing large datasets.

    ⚡ Bolt Optimization: Return only the DataFrame and discard the separate 'iterations' Series.
    Expected Performance Impact: Streamlit's @st.cache_data serializes and stores deep copies
    of all returned values. Returning the DataFrame alongside its standalone index essentially
    doubles memory usage and serialization overhead. The index is already attached to the DataFrame.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file_path = Path(temp_dir) / file_name
        with open(temp_file_path, "wb") as f:
            f.write(_file_content)
        data, _ = fs.pre_parse(temp_file_path)
        return data


def main() -> None:
    """Main function to run the Streamlit application."""
    if 'processed_files' not in st.session_state:
        st.session_state.processed_files = set()

    st.header("Plot OpenFOAM Residuals")

    # Sidebar controls
    with st.sidebar:
        st.subheader("📈 Static Plot Settings")
        width = st.number_input('Figure Width', min_value=1, value=10, help="Width of the static plot in inches.")
        height = st.number_input('Figure Height', min_value=1, value=4, help="Height of the static plot in inches.")
        dpi = st.number_input('Figure DPI', min_value=50, max_value=600, value=150, help="Resolution of the static plot. Lower values render faster.")

        st.divider()

        st.subheader("⚙️ General Settings")
        show_filenames = st.checkbox('Show Filenames', value=False, help="Display the filename above each plot when comparing multiple files.")

    # File uploader
    files = st.file_uploader(
        "Upload 'residual.dat' files here",
        type=['dat'],
        accept_multiple_files=True,
        help="Files should be located in the _postProcessing_ folder of the OpenFOAM case."
    )

    if files:
        # Parse files once and cache results to reduce redundant file reading
        # Expected Performance Impact: Reduces disk I/O and parsing overhead by ~66% (3 reads to 1)
        parsed_files = []
        with st.spinner("Processing files..."):
            for file in files:
                try:
                    data = parse_uploaded_file(file.name, file.file_id, file.getvalue())
                    parsed_files.append({'name': file.name, 'data': data, 'file_id': file.file_id})
                except Exception:
                    st.error(f"Error parsing '{file.name}'. Please ensure it is a valid OpenFOAM residual file.")

        if not parsed_files:
            return

        new_file_ids = {f['file_id'] for f in parsed_files}
        if new_file_ids - st.session_state.processed_files:
            st.toast("Files processed successfully!", icon="✅")
            st.session_state.processed_files = new_file_ids

        # Create tabs
        tab1, tab2, tab3 = st.tabs([
            "📊 Interactive Plot",
            "📈 Static Plot",
            "📋 Raw Data"
        ])

        # Altair plots
        with tab1:
            for i, item in enumerate(parsed_files):
                if i > 0:
                    st.divider()
                if show_filenames:
                    st.subheader(f"File: {item['name']}")
                chart = create_altair_plot(item['data'])
                st.altair_chart(chart, use_container_width=True)

        # Matplotlib plots
        with tab2:
            for i, item in enumerate(parsed_files):
                if i > 0:
                    st.divider()
                if show_filenames:
                    st.subheader(f"File: {item['name']}")
                data = item['data']

                # ⚡ Bolt Optimization: The O(N) array calculations are now performed
                # inside the cached `get_matplotlib_image_bytes` function to prevent redundant
                # execution on every UI interaction cache hit.
                img_bytes = get_matplotlib_image_bytes(data, item['file_id'], width, height, dpi)
                st.image(img_bytes)

        # Raw data
        with tab3:
            for i, item in enumerate(parsed_files):
                if i > 0:
                    st.divider()
                if show_filenames:
                    st.subheader(f"File: {item['name']}")
                st.dataframe(item['data'], use_container_width=True)
    else:
        st.info("👋 Welcome! Please upload your `residual.dat` files using the uploader above to get started.")


if __name__ == "__main__":
    main()