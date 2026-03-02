## 2026-02-28 - Empty State Implementation
**Learning:** The Streamlit file uploader returns `None` or an empty list when no files are uploaded. This provides a natural branching point (`if files:` vs `else:`) to implement an empty state without complex state management.
**Action:** Always check if a file uploader or similar input has data before rendering the main UI, and provide an `st.info` or similar call-to-action when it's empty to guide the user.

## 2025-03-02 - Altair Chart Interactivity in Streamlit
**Learning:** Altair charts rendered in Streamlit are static by default, meaning users cannot zoom or pan through large datasets (like thousands of residual iterations). Adding `.interactive()` to the Altair chart object transforms it into a fully explorable visualization.
**Action:** When using Altair in Streamlit for timeseries or large datasets where exploration is key, always chain `.interactive()` to the chart definition. Additionally, explicitly format tooltips for tiny numbers (e.g., `alt.Tooltip('Value:Q', format='.2e')`) to maintain readability.
