import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import math
import altair as alt

# Page configuration
st.set_page_config(layout="wide")
st.header("Plot OpenFOAM Residuals")

# Helper functions
def order_of_magnitude(number):
    return math.floor(math.log10(number))

def roundup(x):
    return int(math.ceil(x / 100.0)) * 100

def pre_parse(content):
    """Parse OpenFOAM residuals file content and return formatted data"""
    from io import StringIO
    
    # If content is a list of lines, join them
    if isinstance(content, list):
        content_str = '\n'.join(content)
    else:
        content_str = content
    
    raw_data = pd.read_csv(StringIO(content_str), skiprows=1, delimiter=r'\s+')
    iterations = raw_data['#']
    data = raw_data.iloc[:, 1:].shift(+1, axis=1).drop(["Time"], axis=1)
    data = data.set_index(iterations)
    data = data.iloc[1:, :]
    data = data.dropna(axis=1, how="all")          # keeps only columns that have at least one non-NaN
    
    return data, iterations

def create_altair_plot(data):
    """Create Altair visualization"""
    data_melted = data.reset_index().melt(
        id_vars=['#'],
        value_vars=['Ux', 'Uy', 'Uz', 'p', 'epsilon', 'k'],
        var_name='Residual',
        value_name='Value'
    )
    
    chart = alt.Chart(data_melted).mark_line(point=False).encode(
        x=alt.X('#:Q', title='Iteration'),
        y=alt.Y('Value:Q', scale=alt.Scale(type='log'), title='Residuals'),
        color=alt.Color('Residual:N', title='Variable'),
        tooltip=['#', 'Residual', 'Value']
    ).properties(
        width=800,
        height=400
    )
    
    return chart

def create_matplotlib_plot(data, width, height, min_residual, max_iter):
    """Create Matplotlib visualization"""
    plt.rcParams['figure.figsize'] = [int(width), int(height)]
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
    
    # Altair plots
    with tab1:
        for file in files:
            if show_filenames:
                st.subheader(f"File: {file.name}")
            
            # Read and decode UploadedFile content
            file.seek(0)
            content_bytes = file.read()
            content_str = content_bytes.decode('utf-8')
            lines = content_str.split('\n')
            
            data, iterations = pre_parse(lines)
            chart = create_altair_plot(data)
            st.altair_chart(chart)
    
    # Matplotlib plots
    with tab2:
        for file in files:
            if show_filenames:
                st.subheader(f"File: {file.name}")
            
            # Read and decode UploadedFile content
            file.seek(0)
            content_bytes = file.read()
            content_str = content_bytes.decode('utf-8')
            lines = content_str.split('\n')
            
            data, iterations = pre_parse(lines)
            min_residual = math.pow(10, order_of_magnitude(data.min().min()))
            max_iter = data.index.max()
            fig = create_matplotlib_plot(data, width, height, min_residual, max_iter)
            st.pyplot(fig)
            plt.close()
    
    # Raw data
    with tab3:
        for file in files:
            if show_filenames:
                st.subheader(f"File: {file.name}")
            
            # Read and decode UploadedFile content
            file.seek(0)
            content_bytes = file.read()
            content_str = content_bytes.decode('utf-8')
            lines = content_str.split('\n')
            
            data, iterations = pre_parse(lines)
            st.dataframe(data)
