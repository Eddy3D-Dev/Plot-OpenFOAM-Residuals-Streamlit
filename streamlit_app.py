from __future__ import annotations

import hashlib
import io
import json
import math
import traceback
import re
import itertools
import zipfile
from pathlib import Path

import altair as alt
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

FEATURE_COLUMNS = ["Ux", "Uy", "Uz", "p", "epsilon", "k"]
SEO_TITLE = "OpenFOAM Residual Plotter - Plot .dat and .log Files Online"
SEO_DESCRIPTION = (
    "OpenFOAM residual plotter built with Streamlit. Upload .dat and .log files to "
    "visualize CFD convergence with interactive Altair charts, static Matplotlib plots, "
    "tables, CSV export, and image ZIP export."
)
SEO_CANONICAL_URL = "https://plot-openfoam-residuals.streamlit.app/"
SEO_IMAGE_URL = "https://plot-openfoam-residuals.streamlit.app/app/static/favicon.png"
TIME_RE = re.compile(
    r"^\s*Time\s*=\s*(?P<time>[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)\s*$"
)
SOLVE_RE = re.compile(
    r"Solving for (?P<field>[^,]+),\s*Initial residual\s*=\s*(?P<residual>[^,]+),"
)


def parse_numeric(value: str) -> float:
    raw = value.strip()
    if not raw or raw.upper() == "N/A":
        return float("nan")
    try:
        return float(raw)
    except ValueError:
        return float("nan")


def parse_residual_dat(raw_text: str) -> pd.DataFrame:
    lines = raw_text.splitlines()
    header: list[str] | None = None

    for line in lines:
        if re.match(r"^\s*#\s*Time(?:\s|$)", line):
            header = line.replace("#", " ").split()
            break

    if not header:
        raise ValueError('Expected a "# Time" header row in this .dat file.')

    try:
        time_index = header.index("Time")
    except ValueError as exc:
        raise ValueError('Expected a "Time" column in this .dat file.') from exc

    value_columns = [name for i, name in enumerate(header) if i != time_index]
    time_values: list[float] = []
    row_values: dict[str, list[float]] = {name: [] for name in value_columns}

    for line_number, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        fields = stripped.split()
        if len(fields) > len(header):
            raise ValueError(
                f"Data row {line_number} has more values than header columns."
            )

        time_values.append(parse_numeric(fields[time_index] if time_index < len(fields) else ""))
        for column_index, column_name in enumerate(header):
            if column_index == time_index:
                continue
            cell = fields[column_index] if column_index < len(fields) else ""
            row_values[column_name].append(parse_numeric(cell))

    if not time_values:
        raise ValueError("No data rows found in this .dat file.")

    data = pd.DataFrame(row_values, index=time_values)
    data.index.name = "Time"
    data = data.dropna(axis=1, how="all")
    if data.empty:
        raise ValueError("No numeric residual columns found in this .dat file.")
    return data


def parse_openfoam_log(raw_text: str) -> pd.DataFrame:
    rows: list[dict[str, float]] = []
    indices: list[float] = []
    current_row: dict[str, float] | None = None
    current_index: float | None = None
    fallback_index = 0
    has_explicit_time_markers = any(TIME_RE.match(line) for line in raw_text.splitlines())
    explicit_step_index = 0

    def flush_current_row() -> None:
        nonlocal fallback_index
        if not current_row:
            return
        rows.append(current_row)
        if current_index is not None and pd.notna(current_index):
            indices.append(float(current_index))
        else:
            indices.append(float(fallback_index))
            fallback_index += 1

    for line in raw_text.splitlines():
        time_match = TIME_RE.match(line)
        if time_match:
            flush_current_row()
            current_row = {}
            # Use monotonic step index for .log parsing to match "Iterations"
            # axis semantics and avoid artifacts when simulation time repeats.
            current_index = float(explicit_step_index)
            explicit_step_index += 1
            continue

        match = SOLVE_RE.search(line)
        if match is None:
            continue

        if current_row is None:
            current_row = {}
            current_index = None

        field = match.group("field").strip()
        residual = parse_numeric(match.group("residual"))
        if pd.isna(residual):
            continue

        if field in current_row:
            if has_explicit_time_markers:
                # Keep one row per explicit time step; ignore duplicate field solves.
                continue
            # Logs without explicit time markers: repeated fields imply new row.
            flush_current_row()
            current_row = {}
            current_index = None

        current_row[field] = float(residual)

    flush_current_row()

    if not rows:
        raise ValueError("No OpenFOAM residual entries were found in this log file.")

    data = pd.DataFrame(rows, index=indices)
    data.index.name = "Time"
    data = data.dropna(axis=1, how="all")
    if data.empty:
        raise ValueError("No numeric residual columns found in this log file.")
    return data


def parse_residual_file(raw_text: str, filename: str) -> pd.DataFrame:
    lower_name = filename.lower()
    prefer_dat_by_name = lower_name.endswith(".dat")
    prefer_log_by_name = lower_name.endswith((".log", ".out", ".txt"))
    has_dat_header = bool(re.search(r"^\s*#\s*Time(?:\s|$)", raw_text, flags=re.MULTILINE))
    has_log_time = bool(
        re.search(
            r"(?:^|\n)\s*Time\s*=\s*[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?",
            raw_text,
            flags=re.MULTILINE,
        )
    )
    has_log_solver = bool(re.search(r"Solving for\s+[^,]+,\s*Initial residual\s*=", raw_text))

    looks_like_log = has_log_time or has_log_solver
    if looks_like_log and not has_dat_header:
        primary, fallback = parse_openfoam_log, parse_residual_dat
    elif has_dat_header and not looks_like_log:
        primary, fallback = parse_residual_dat, parse_openfoam_log
    elif prefer_dat_by_name:
        primary, fallback = parse_residual_dat, parse_openfoam_log
    elif prefer_log_by_name:
        primary, fallback = parse_openfoam_log, parse_residual_dat
    else:
        primary, fallback = parse_openfoam_log, parse_residual_dat

    try:
        return primary(raw_text)
    except Exception as primary_error:
        try:
            return fallback(raw_text)
        except Exception:
            raise primary_error


def build_long_frame(data: pd.DataFrame) -> pd.DataFrame:
    frame = data.reset_index().melt(
        id_vars=["Time"],
        var_name="Variable",
        value_name="Residual",
    )
    frame["Time"] = pd.to_numeric(frame["Time"], errors="coerce")
    frame["Residual"] = pd.to_numeric(frame["Residual"], errors="coerce")
    frame = frame.dropna(subset=["Time", "Residual"])
    frame = frame[frame["Residual"] > 0]
    return frame


def build_chart(data: pd.DataFrame, *, interactive: bool, height: int, accessible_line_styles: bool = True) -> alt.Chart | None:
    long_frame = build_long_frame(data)
    if long_frame.empty:
        return None

    ordered_cols = [c for c in FEATURE_COLUMNS if c in data.columns]
    ordered_cols.extend([c for c in data.columns if c not in ordered_cols])

    selection = alt.selection_point(fields=["Variable"], bind="legend")
    hover = alt.selection_point(
        fields=["Variable"],
        on="pointerover",
        empty=False,
        clear="pointerout"
    )

    encode_args = {
        "x": alt.X("Time:Q", title="Iterations", scale=alt.Scale(zero=False)),
        "y": alt.Y(
            "Residual:Q",
            title="Residuals",
            scale=alt.Scale(type="log"),
            axis=alt.Axis(format="e"),
        ),
        "color": alt.Color(
            "Variable:N",
            sort=ordered_cols,
            legend=alt.Legend(title=["Variable", "(click to isolate,", "shift-click to multi-select)"])
        ),
        "opacity": alt.condition(selection, alt.value(1.0), alt.value(0.2)),
        "strokeWidth": alt.condition(hover, alt.value(3), alt.value(1.5)),
        "tooltip": [
            alt.Tooltip("Time:Q", title="Iteration", format=".6g"),
            alt.Tooltip("Variable:N", title="Variable"),
            alt.Tooltip("Residual:Q", title="Residual", format=".6e"),
        ],
    }

    if accessible_line_styles:
        encode_args["color"] = alt.Color(
            "Variable:N",
            sort=ordered_cols,
            legend=alt.Legend(title=["Variable", "(click to isolate,", "shift-click to multi-select)"]),
            scale=alt.Scale(scheme="dark2"),
        )
        encode_args["strokeDash"] = alt.StrokeDash(
            "Variable:N",
            sort=ordered_cols,
            legend=alt.Legend(title=["Variable", "(click to isolate,", "shift-click to multi-select)"])
        )

    chart = (
        alt.Chart(long_frame)
        .mark_line(cursor="pointer")
        .encode(**encode_args)
        .add_params(selection, hover)
        .properties(
            height=height,
            description=f"Interactive line chart showing OpenFOAM residual convergence over iterations for variables: {', '.join(ordered_cols)}. Use the legend to isolate specific variables, or shift-click to select multiple."
        )
    )

    if interactive:
        return chart.interactive(bind_y=False)
    return chart


def build_matplotlib_figure(data: pd.DataFrame, *, height_pixels: int, show_grid: bool, accessible_line_styles: bool = True) -> plt.Figure | None:
    time_values = pd.to_numeric(data.index.to_series(), errors="coerce")
    ordered_cols = [c for c in FEATURE_COLUMNS if c in data.columns]
    ordered_cols.extend([c for c in data.columns if c not in ordered_cols])

    fig_height = max(2.4, height_pixels / 100.0)

    style = "tableau-colorblind10" if accessible_line_styles else "default"
    with plt.style.context(style):
        fig, ax = plt.subplots(figsize=(10, fig_height))
        has_series = False

        if accessible_line_styles:
            line_styles = itertools.cycle(["-", "--", "-.", ":"])
        else:
            line_styles = itertools.cycle(["-"])

        for column in ordered_cols:
            residual = pd.to_numeric(data[column], errors="coerce")
            mask = time_values.notna() & residual.notna() & (residual > 0)
            if not mask.any():
                continue
            ax.plot(time_values[mask], residual[mask], label=column, linewidth=2, linestyle=next(line_styles))
            has_series = True

        if not has_series:
            plt.close(fig)
            return None

        ax.set_xlabel("Iterations")
        ax.set_ylabel("Residuals")
        ax.set_yscale("log")
        if show_grid:
            ax.grid(True, which="both", linestyle="--", linewidth=0.5, alpha=0.4)
        ax.legend(loc="best")
        fig.tight_layout()
        return fig


def figure_to_png_bytes(figure: plt.Figure, *, dpi: int = 200) -> bytes:
    buffer = io.BytesIO()
    figure.savefig(buffer, format="png", dpi=dpi, bbox_inches="tight")
    return buffer.getvalue()


def sanitize_stem(name: str) -> str:
    stem = Path(name).stem
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", stem).strip("._")
    return stem or "plot"


def build_zip(items: list[tuple[str, bytes]], suffix_name: str, ext: str) -> bytes:
    buffer = io.BytesIO()
    used_names: dict[str, int] = {}

    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        for original_name, file_bytes in items:
            base_name = f"{sanitize_stem(original_name)}_{suffix_name}"
            index = used_names.get(base_name, 0)
            used_names[base_name] = index + 1
            suffix = f"_{index + 1}" if index else ""
            archive.writestr(f"{base_name}{suffix}.{ext}", file_bytes)

    return buffer.getvalue()


def inject_seo_metadata() -> None:
    json_ld = {
        "@context": "https://schema.org",
        "@type": "WebApplication",
        "name": "OpenFOAM Residual Plotter",
        "url": SEO_CANONICAL_URL,
        "applicationCategory": "EngineeringApplication",
        "operatingSystem": "Any",
        "description": SEO_DESCRIPTION,
        "featureList": [
            "OpenFOAM .dat parser",
            "OpenFOAM .log parser",
            "Interactive Altair residual charts",
            "Static Matplotlib residual charts",
            "CSV export",
            "ZIP image export",
        ],
    }

    payload = {
        "title": SEO_TITLE,
        "description": SEO_DESCRIPTION,
        "canonical": SEO_CANONICAL_URL,
        "image": SEO_IMAGE_URL,
        "jsonLd": json_ld,
    }

    script = f"""
    <script>
    (function() {{
      const payload = {json.dumps(payload)};
      const doc = (window.parent && window.parent.document) ? window.parent.document : document;

      function upsertMeta(attr, key, content) {{
        if (!content) return;
        let el = doc.head.querySelector(`meta[${{attr}}="${{key}}"]`);
        if (!el) {{
          el = doc.createElement("meta");
          el.setAttribute(attr, key);
          doc.head.appendChild(el);
        }}
        el.setAttribute("content", content);
      }}

      doc.title = payload.title;
      upsertMeta("name", "description", payload.description);
      upsertMeta("name", "keywords", "OpenFOAM residual plotter, OpenFOAM .log parser, OpenFOAM .dat parser, CFD convergence plotting, Streamlit OpenFOAM");
      upsertMeta("name", "robots", "index, follow");
      upsertMeta("property", "og:type", "website");
      upsertMeta("property", "og:title", payload.title);
      upsertMeta("property", "og:description", payload.description);
      upsertMeta("property", "og:url", payload.canonical);
      upsertMeta("property", "og:image", payload.image);
      upsertMeta("name", "twitter:card", "summary_large_image");
      upsertMeta("name", "twitter:title", payload.title);
      upsertMeta("name", "twitter:description", payload.description);
      upsertMeta("name", "twitter:image", payload.image);

      let canonical = doc.head.querySelector('link[rel="canonical"]');
      if (!canonical) {{
        canonical = doc.createElement("link");
        canonical.setAttribute("rel", "canonical");
        doc.head.appendChild(canonical);
      }}
      canonical.setAttribute("href", payload.canonical);

      let ld = doc.head.querySelector('script[type="application/ld+json"][data-pofr-seo="1"]');
      if (!ld) {{
        ld = doc.createElement("script");
        ld.type = "application/ld+json";
        ld.setAttribute("data-pofr-seo", "1");
        doc.head.appendChild(ld);
      }}
      ld.textContent = JSON.stringify(payload.jsonLd);
    }})();
    </script>
    """

    components.html(script, height=0, width=0)


def make_file_id(name: str, raw_bytes: bytes) -> str:
    digest = hashlib.sha1(raw_bytes, usedforsecurity=False).hexdigest()[:12]
    return f"{name}-{digest}"


def get_file_icon(filename: str) -> str:
    return ":material/article:" if filename.lower().endswith((".log", ".out", ".txt")) else ":material/description:"


def main() -> None:
    st.set_page_config(page_title=SEO_TITLE, page_icon="📈")
    st.logo("https://raw.githubusercontent.com/FortAwesome/Font-Awesome/6.x/svgs/solid/chart-line.svg", link=SEO_CANONICAL_URL)
    inject_seo_metadata()
    st.title(":material/monitoring: Plot OpenFOAM Residuals")
    st.caption(
        "Upload OpenFOAM residual `.dat` and `.log` files to analyze CFD convergence "
        "with interactive and static residual plots."
    )
    st.markdown(
        """
        This OpenFOAM residual plotter helps CFD engineers inspect solver convergence for
        variables like `Ux`, `Uy`, `Uz`, `p`, `k`, and `epsilon`. Upload files, compare runs,
        and export data or images for reports.
        """
    )

    uploaded_files = st.file_uploader(
        ":material/upload_file: Upload OpenFOAM residual files",
        type=["dat", "log", "txt"],
        accept_multiple_files=True,
        help="Upload multiple .dat or .log files to compare convergence side-by-side.",
    )

    if "use_sample_data" not in st.session_state:
        st.session_state.use_sample_data = False

    if uploaded_files:
        st.session_state.use_sample_data = False

    has_files = bool(uploaded_files) or st.session_state.use_sample_data
    disabled_help = "⚠️ Please upload a residual file first to enable this setting."

    # To determine if we should force showing filenames, we must inspect the files to be processed
    # before rendering the sidebar toggle.
    files_to_process = []
    if st.session_state.use_sample_data and not uploaded_files:
        class DummyFile:
            def __init__(self, name: str, data: bytes):
                self.name = name
                self._data = data
            def getvalue(self) -> bytes:
                return self._data

        sample_path = Path(__file__).parent / "test_residual.dat"
        with open(sample_path, "rb") as f:
            sample_data = f.read()
        files_to_process = [DummyFile("test_residual.dat", sample_data)]
    else:
        files_to_process = uploaded_files

    # Force show filenames if we have > 1 files to process
    force_show_names = len(files_to_process) > 1

    with st.sidebar:
        st.header(":material/settings: Plot Settings")

        st.markdown("#### :material/visibility: Display Options")
        show_filenames = st.toggle(
            "Show filenames",
            value=force_show_names,
            disabled=force_show_names or not has_files,
            help="Filenames are always shown when comparing multiple files." if force_show_names else ("Show the filename above each plot." if has_files else disabled_help),
        )
        st.divider()

        st.markdown("#### :material/straighten: Plot Dimensions")
        interactive_height = st.slider(
            "Interactive plot height", 240, 900, 420, 20,
            format="%d px",
            disabled=not has_files,
            help="Adjust the vertical size (in pixels) of the interactive charts." if has_files else disabled_help
        )
        static_height = st.slider(
            "Static plot height", 240, 900, 360, 20,
            format="%d px",
            disabled=not has_files,
            help="Adjust the vertical size (in pixels) of the static plots." if has_files else disabled_help
        )

        st.divider()
        st.markdown("#### :material/accessibility_new: Styling & Accessibility")
        show_grid = st.toggle(
            "Show static grid",
            value=True,
            disabled=not has_files,
            help="Displays subtle grid lines on both major and minor ticks to improve readability on logarithmic scales." if has_files else disabled_help,
        )
        accessible_line_styles = st.toggle(
            "Use accessible line styles",
            value=True,
            disabled=not has_files,
            help="Combines colors with different line styles to ensure both interactive and static plots are readable for colorblind users and in black-and-white." if has_files else disabled_help,
        )

    if not has_files:
        st.info("Upload one or more OpenFOAM residual files to start. Supported formats:", icon=":material/upload_file:")
        tab_dat, tab_log = st.tabs([":material/description: .dat Example", ":material/article: .log Example"])
        with tab_dat:
            st.code("# OpenFOAM\n# Time alpha beta gamma\n1 0.1 0.2 0.3\n2 0.01 0.02 0.03", language="text", wrap_lines=True)
        with tab_log:
            st.code("Time = 1\nSolving for Ux, Initial residual = 0.1, Final residual = 0.01, No Iterations 10\nSolving for Uy, Initial residual = 0.2, Final residual = 0.02, No Iterations 10", language="text", wrap_lines=True)

        # Load sample data robustly using path relative to this script
        sample_path = Path(__file__).parent / "test_residual.dat"
        with open(sample_path, "rb") as f:
            sample_data = f.read()

        col1, col2 = st.columns(2)
        with col1:
            if st.button(
                "Load sample data",
                icon=":material/play_circle:",
                type="primary",
                use_container_width=True,
                help="Instantly load sample data to see how the app works.",
            ):
                st.session_state.use_sample_data = True
                st.rerun()
        with col2:
            st.download_button(
                label="Download sample file",
                data=sample_data,
                file_name="sample_residual.dat",
                mime="text/plain",
                icon=":material/download:",
                use_container_width=True,
                help="Download a sample OpenFOAM residual file to test the application.",
            )
        return

    if st.session_state.use_sample_data and not uploaded_files:
        st.info("Currently viewing sample data.", icon=":material/visibility:")
        if st.button("Clear sample data", icon=":material/close:", use_container_width=True, help="Clear the sample data to upload your own files."):
            st.session_state.use_sample_data = False
            st.rerun()

    parsed_items: list[dict[str, object]] = []
    errors: list[tuple[str, str, str]] = []

    with st.spinner("Processing files..."):
        for uploaded in files_to_process:
            raw_bytes = uploaded.getvalue()
            text = raw_bytes.decode("utf-8", errors="replace")
            try:
                data = parse_residual_file(text, uploaded.name)
                parsed_items.append(
                    {
                        "name": uploaded.name,
                        "file_id": make_file_id(uploaded.name, raw_bytes),
                        "data": data,
                    }
                )
            except Exception as exc:
                errors.append((uploaded.name, str(exc), traceback.format_exc()))

    if "processed_file_ids" not in st.session_state:
        st.session_state.processed_file_ids = set()

    new_file_ids = {str(item["file_id"]) for item in parsed_items} - st.session_state.processed_file_ids
    if new_file_ids:
        st.toast(f"Successfully processed {len(new_file_ids)} new file(s)!", icon="🎉")
        st.session_state.processed_file_ids.update(new_file_ids)

    for filename, message, tb in errors:
        st.error(f"**{filename}**: {message}", icon=":material/error:")
        with st.expander("View error details", icon=":material/bug_report:"):
            st.code(tb, language="python", wrap_lines=True)

    if not parsed_items:
        return

    tab_interactive, tab_static, tab_table = st.tabs([":material/show_chart: Interactive Plot", ":material/image: Static Plot", ":material/table_view: Raw Data"])

    with tab_interactive:
        st.caption(
            ":material/lightbulb: **Tip:** Scroll to zoom the X-axis (Iterations) and drag to pan. "
            "Vertical zooming is disabled to preserve the log-scale perspective. Double-click to reset the view."
        )
        for idx, item in enumerate(parsed_items):
            name = str(item["name"])
            file_id = str(item["file_id"])
            data = item["data"]
            if show_filenames:
                st.subheader(f"{get_file_icon(name)} {name}")
            chart = build_chart(data, interactive=True, height=interactive_height, accessible_line_styles=accessible_line_styles)
            if chart is None:
                st.warning(f"{name}: no positive residual values to chart (log-scale requires strictly positive values).", icon=":material/warning:")
            else:
                st.altair_chart(chart, width="stretch")
            if idx < len(parsed_items) - 1:
                st.divider()

    with tab_static:
        st.caption(
            ":material/image: **Static Plots:** These high-resolution Matplotlib figures are ideal for "
            "reports and publications. Use the sidebar to adjust their dimensions and styling."
        )
        static_images: list[tuple[str, bytes]] = []

        for idx, item in enumerate(parsed_items):
            name = str(item["name"])
            file_id = str(item["file_id"])
            data = item["data"]
            if show_filenames:
                st.subheader(f"{get_file_icon(name)} {name}")
            figure = build_matplotlib_figure(
                data,
                height_pixels=static_height,
                show_grid=show_grid,
                accessible_line_styles=accessible_line_styles,
            )
            if figure is None:
                st.warning(f"{name}: no positive residual values to chart (log-scale requires strictly positive values).", icon=":material/warning:")
            else:
                png_bytes = figure_to_png_bytes(figure)
                static_images.append((name, png_bytes))
                st.image(png_bytes, caption=f"Static residual plot for {name}", use_container_width=True)
                plt.close(figure)
                st.download_button(
                    f"Download Plot Image ({name})",
                    data=png_bytes,
                    file_name=f"{Path(name).stem}.png",
                    mime="image/png",
                    key=f"static_png_{file_id}",
                    icon=":material/image:",
                    help="Download this static plot as a PNG image.",
                    use_container_width=True,
                )
            if idx < len(parsed_items) - 1:
                st.divider()

        if len(static_images) > 1:
            st.divider()
            st.download_button(
                "Export all static images (.zip)",
                data=build_zip(static_images, "static", "png"),
                file_name="openfoam_residual_static_plots.zip",
                mime="application/zip",
                key="export_all_static_images_zip",
                icon=":material/folder_zip:",
                help="Download all static plot images as a single ZIP archive.",
                type="primary",
                use_container_width=True,
            )

    with tab_table:
        st.caption(
            ":material/table_view: **Raw Data & Metrics:** Inspect the final convergence metrics and raw "
            "residual values. Export the data to CSV for further analysis."
        )
        all_csvs: list[tuple[str, bytes]] = []
        for idx, item in enumerate(parsed_items):
            name = str(item["name"])
            file_id = str(item["file_id"])
            data = item["data"]
            if show_filenames:
                st.subheader(f"{get_file_icon(name)} {name}")

            st.markdown("#### :material/summarize: Final Convergence Summary")
            valid_cols = [c for c in data.columns if not data[c].dropna().empty]

            for i in range(0, len(valid_cols), 4):
                cols = st.columns(4)
                for j, col in enumerate(valid_cols[i:i+4]):
                    clean_series = data[col].dropna()
                    first_val = float(clean_series.iloc[0])
                    final_val = float(clean_series.iloc[-1])
                    diff = final_val - first_val
                    if final_val > 0 and first_val > 0:
                        oom_diff = math.log10(final_val) - math.log10(first_val)
                        delta_str = f"{oom_diff:+.2f} OoM"
                    else:
                        delta_str = f"{diff:.2e}"

                    sparkline_data = [math.log10(v) for v in clean_series.tolist() if v > 0]
                    sparkline_data = sparkline_data[::max(1, len(sparkline_data) // 100)]

                    with cols[j]:
                        st.metric(
                            label=col,
                            value=f"{final_val:.2e}",
                            delta=delta_str,
                            delta_color="inverse",
                            border=True,
                            chart_data=sparkline_data,
                            help=f"Change from initial iteration ({first_val:.4e}). 'OoM' indicates Orders of Magnitude.",
                        )

            col_config = {c: st.column_config.NumberColumn(format="%.4e", help=f"Residual values for the '{c}' field") for c in valid_cols}
            col_config["Time"] = st.column_config.NumberColumn("Iterations", format="%g", help="Simulation step or iteration number")
            st.dataframe(
                data.reset_index(),
                width="stretch",
                height=360,
                column_config=col_config,
                hide_index=True,
            )
            csv_buffer = io.StringIO()
            data.to_csv(csv_buffer)
            csv_bytes = csv_buffer.getvalue().encode("utf-8")
            all_csvs.append((name, csv_bytes))
            st.download_button(
                f"Download CSV ({name})",
                data=csv_bytes,
                file_name=f"{Path(name).stem}.csv",
                mime="text/csv",
                key=f"table_csv_{file_id}",
                icon=":material/download:",
                help="Download the raw residual data as a CSV file.",
                use_container_width=True,
            )
            if idx < len(parsed_items) - 1:
                st.divider()

        if len(all_csvs) > 1:
            st.divider()
            st.download_button(
                "Export all data (.zip)",
                data=build_zip(all_csvs, "data", "csv"),
                file_name="openfoam_residual_data.zip",
                mime="application/zip",
                key="export_all_data_zip",
                icon=":material/folder_zip:",
                help="Download all raw residual data as a single ZIP archive.",
                type="primary",
                use_container_width=True,
            )

    with st.expander("FAQ: OpenFOAM Residual Plotting", icon=":material/help:"):
        st.markdown(
            """
            #### :material/file_present: What files are supported?
            OpenFOAM residual `.dat`, `.log`, and `.txt` files that contain solver residual entries.

            #### :material/show_chart: Are residual plots on log scale?
            Yes. Interactive and static plots use a logarithmic residual axis for convergence analysis.

            #### :material/download: Can I export outputs?
            Yes. Export per-file CSV tables and download all static plot images as a ZIP file.
            """
        )


if __name__ == "__main__":
    main()
