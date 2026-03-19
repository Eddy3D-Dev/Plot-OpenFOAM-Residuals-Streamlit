from __future__ import annotations

import hashlib
import io
import re
from pathlib import Path

import altair as alt
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

FEATURE_COLUMNS = ["Ux", "Uy", "Uz", "p", "epsilon", "k"]
TIME_RE = re.compile(
    r"(?:^|\s)Time\s*=\s*(?P<time>[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)"
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
        time_match = TIME_RE.search(line)
        if time_match:
            flush_current_row()
            current_row = {}
            parsed_time = parse_numeric(time_match.group("time"))
            current_index = float(parsed_time) if pd.notna(parsed_time) else None
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


def build_chart(data: pd.DataFrame, *, interactive: bool, height: int) -> alt.Chart | None:
    long_frame = build_long_frame(data)
    if long_frame.empty:
        return None

    ordered_cols = [c for c in FEATURE_COLUMNS if c in data.columns]
    ordered_cols.extend([c for c in data.columns if c not in ordered_cols])

    chart = (
        alt.Chart(long_frame)
        .mark_line()
        .encode(
            x=alt.X("Time:Q", title="Iterations"),
            y=alt.Y(
                "Residual:Q",
                title="Residuals",
                scale=alt.Scale(type="log"),
            ),
            color=alt.Color("Variable:N", sort=ordered_cols),
            tooltip=[
                alt.Tooltip("Time:Q", format=".6g"),
                alt.Tooltip("Variable:N"),
                alt.Tooltip("Residual:Q", format=".6e"),
            ],
        )
        .properties(height=height)
    )

    if interactive:
        return chart.interactive()
    return chart


def build_matplotlib_figure(data: pd.DataFrame, *, height_pixels: int, show_grid: bool) -> plt.Figure | None:
    time_values = pd.to_numeric(data.index.to_series(), errors="coerce")
    ordered_cols = [c for c in FEATURE_COLUMNS if c in data.columns]
    ordered_cols.extend([c for c in data.columns if c not in ordered_cols])

    fig_height = max(2.4, height_pixels / 100.0)
    fig, ax = plt.subplots(figsize=(10, fig_height))
    has_series = False

    for column in ordered_cols:
        residual = pd.to_numeric(data[column], errors="coerce")
        mask = time_values.notna() & residual.notna() & (residual > 0)
        if not mask.any():
            continue
        ax.plot(time_values[mask], residual[mask], label=column, linewidth=2)
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


def make_file_id(name: str, raw_bytes: bytes) -> str:
    digest = hashlib.sha1(raw_bytes, usedforsecurity=False).hexdigest()[:12]
    return f"{name}-{digest}"


def main() -> None:
    st.set_page_config(page_title="Plot OpenFOAM Residuals", layout="wide")
    st.title("Plot OpenFOAM Residuals")
    st.caption("Upload OpenFOAM residual `.dat` or `.log` files.")

    uploaded_files = st.file_uploader(
        "Select files",
        type=["dat", "log", "txt"],
        accept_multiple_files=True,
    )

    if not uploaded_files:
        st.info("Upload one or more OpenFOAM residual files to start.")
        return

    parsed_items: list[dict[str, object]] = []
    errors: list[tuple[str, str]] = []

    for uploaded in uploaded_files:
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
            errors.append((uploaded.name, str(exc)))

    ok_count = len(parsed_items)
    err_count = len(errors)
    st.write(f"{len(uploaded_files)} files selected: {ok_count} parsed, {err_count} failed.")

    for filename, message in errors:
        st.error(f"{filename}: {message}")

    if not parsed_items:
        return

    show_names_default = len(parsed_items) > 1
    controls = st.columns([1, 1, 1, 1])
    show_filenames = controls[0].checkbox(
        "Show filenames",
        value=show_names_default,
        disabled=show_names_default,
    )
    interactive_height = controls[1].slider("Interactive height", 240, 900, 420, 20)
    static_renderer = controls[2].selectbox(
        "Static renderer",
        options=["Altair", "Matplotlib"],
        index=0,
    )
    static_height = controls[3].slider("Static height", 240, 900, 360, 20)
    show_grid = False
    if static_renderer == "Matplotlib":
        show_grid = st.checkbox("Show grid (Matplotlib)", value=True)

    tab_interactive, tab_static, tab_table = st.tabs(["Interactive", "Static", "Data"])

    with tab_interactive:
        for item in parsed_items:
            name = str(item["name"])
            file_id = str(item["file_id"])
            data = item["data"]
            if show_filenames:
                st.subheader(name)
            chart = build_chart(data, interactive=True, height=interactive_height)
            if chart is None:
                st.warning(f"{name}: no positive residual values to chart.")
            else:
                st.altair_chart(chart, width="stretch")
            csv_bytes = data.to_csv().encode("utf-8")
            st.download_button(
                f"Download CSV ({name})",
                data=csv_bytes,
                file_name=f"{Path(name).stem}.csv",
                mime="text/csv",
                key=f"interactive_csv_{file_id}",
            )

    with tab_static:
        for item in parsed_items:
            name = str(item["name"])
            file_id = str(item["file_id"])
            data = item["data"]
            if show_filenames:
                st.subheader(name)
            if static_renderer == "Matplotlib":
                figure = build_matplotlib_figure(
                    data,
                    height_pixels=static_height,
                    show_grid=show_grid,
                )
                if figure is None:
                    st.warning(f"{name}: no positive residual values to chart.")
                else:
                    st.pyplot(figure)
                    plt.close(figure)
            else:
                chart = build_chart(data, interactive=False, height=static_height)
                if chart is None:
                    st.warning(f"{name}: no positive residual values to chart.")
                else:
                    st.altair_chart(chart, width="stretch")
            csv_bytes = data.to_csv().encode("utf-8")
            st.download_button(
                f"Download CSV ({name})",
                data=csv_bytes,
                file_name=f"{Path(name).stem}.csv",
                mime="text/csv",
                key=f"static_csv_{file_id}",
            )

    with tab_table:
        for item in parsed_items:
            name = str(item["name"])
            file_id = str(item["file_id"])
            data = item["data"]
            if show_filenames:
                st.subheader(name)
            st.dataframe(data.reset_index(), width="stretch", height=360)
            csv_buffer = io.StringIO()
            data.to_csv(csv_buffer)
            st.download_button(
                f"Download CSV ({name})",
                data=csv_buffer.getvalue().encode("utf-8"),
                file_name=f"{Path(name).stem}.csv",
                mime="text/csv",
                key=f"table_csv_{file_id}",
            )


if __name__ == "__main__":
    main()
