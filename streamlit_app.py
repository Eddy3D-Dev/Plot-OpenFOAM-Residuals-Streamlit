import math
import tempfile
from pathlib import Path

import altair as alt
import matplotlib.pyplot as plt
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
    data_melted = data.reset_index().melt(
        id_vars=['Time'],  # Use 'Time' as the identifier variable
        value_vars=['Ux', 'Uy', 'Uz', 'p', 'epsilon', 'k'],
        var_name='Residual',
        value_name='Value'
    )

    chart = alt.Chart(data_melted).mark_line(point=False).encode(
        x=alt.X('Time:Q', title='Iteration'),  # Use the 'Time' column for the x-axis
        y=alt.Y('Value:Q', scale=alt.Scale(type='log'), title='Residuals'),
        color=alt.Color('Residual:N', title='Variable'),
        tooltip=['Time', 'Residual', 'Value']  # Update tooltip to use 'Time'
    ).properties(
        width=800,
        height=400
    )

    return chart


def create_matplotlib_plot(
    data: pd.DataFrame,
    width: int,
    height: int,
    min_residual: float,
    max_iter: int
) -> plt.Figure:
    """
    Create a Matplotlib visualization for the residuals.

    Args:
        data (pd.DataFrame): The dataframe containing residual data.
        width (int): The width of the figure.
        height (int): The height of the figure.
        min_residual (float): The minimum residual value for the y-axis.
        max_iter (int): The maximum iteration number for the x-axis.

    Returns:
        plt.Figure: The Matplotlib figure object.
    """
    plt.rcParams['figure.figsize'] = [width, height]
    plt.rcParams['figure.dpi'] = 600

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
def parse_uploaded_file(file_name: str, file_content: bytes) -> tuple[pd.DataFrame, pd.Series]:
    """
    Parse the uploaded file once and cache the result.
    This avoids redundant I/O and CPU overhead when switching between tabs.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file_path = Path(temp_dir) / file_name
        with open(temp_file_path, "wb") as f:
            f.write(file_content)
        return fs.pre_parse(temp_file_path)


def main() -> None:
    """Main function to run the Streamlit application."""
    st.header("Plot OpenFOAM Residuals")

    # Sidebar controls
    with st.sidebar:
        st.subheader("Plot Settings")
        width = st.number_input('Figure Width', min_value=1, value=10)
        height = st.number_input('Figure Height', min_value=1, value=4)
        show_filenames = st.checkbox('Show Filenames', value=False)

    # File uploader
    files = st.file_uploader(
        "Upload 'residual.dat' files here",
        type=['dat'],
        accept_multiple_files=True,
        help="Files should be located in the _postProcessing_ folder of the OpenFOAM case."
    )

    if files:
        # Create tabs
        tab1, tab2, tab3 = st.tabs([
            "Altair",
            "Matplotlib",
            "Dataframe"
        ])

        # Parse files once and cache results to reduce redundant file reading
        # Expected Performance Impact: Reduces disk I/O and parsing overhead by ~66% (3 reads to 1)
        parsed_files = []
        for file in files:
            data, iterations = parse_uploaded_file(file.name, file.getvalue())
            parsed_files.append({'name': file.name, 'data': data, 'iterations': iterations})

        # Altair plots
        with tab1:
            for item in parsed_files:
                if show_filenames:
                    st.subheader(f"File: {item['name']}")
                chart = create_altair_plot(item['data'])
                st.altair_chart(chart, use_container_width=True)

        # Matplotlib plots
        with tab2:
            for item in parsed_files:
                if show_filenames:
                    st.subheader(f"File: {item['name']}")
                data = item['data']
                min_residual = math.pow(10, orp.order_of_magnitude(data.min().min()))
                max_iter = data.index.max()
                fig = create_matplotlib_plot(data, width, height, min_residual, max_iter)
                st.pyplot(fig)
                plt.close()

        # Raw data
        with tab3:
            for item in parsed_files:
                if show_filenames:
                    st.subheader(f"File: {item['name']}")
                st.dataframe(item['data'])
    else:
        st.info("👋 Welcome! Please upload your `residual.dat` files using the uploader above to get started.")


if __name__ == "__main__":
    main()