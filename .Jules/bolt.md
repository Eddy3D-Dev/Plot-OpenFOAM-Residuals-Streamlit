## 2026-03-01 - Redundant File Parsing in Streamlit Tabs
**Learning:** In Streamlit, uploading a file and rendering it across multiple tabs can lead to redundant I/O and parsing operations (`O(N*T)` where N is files and T is tabs). Previously, `fs.pre_parse` was called three times per uploaded file (once for Altair, once for Matplotlib, once for Dataframe).
**Action:** Use `@st.cache_data` on a wrapper function that handles the file reading and parsing. Parse the file once upon upload, store the result in memory (or caching layer), and reuse the parsed `pd.DataFrame` across all UI components (tabs) to reduce disk I/O and CPU overhead.

## 2026-03-14 - Cache Altair Serialization
**Learning:** Streamlit implicitly calls `chart.to_dict()` on any `alt.Chart` object passed to `st.altair_chart` before sending the spec to the frontend. For large datasets, this recursive JSON serialization blocks the Python main thread for seconds on *every* UI rerun (e.g. checkbox toggles).
**Action:** Extract the `.to_dict()` serialization into a `@st.cache_data` decorated function. Streamlit's `st.altair_chart` natively accepts the serialized Vega-Lite dict. Using an underscore on the dataframe argument (`_data`) bypasses hashing, ensuring serialization only occurs once.
