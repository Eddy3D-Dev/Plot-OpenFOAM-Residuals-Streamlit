## 2026-03-02 - Client-side Data Melting with Altair
**Learning:** In Streamlit applications using Altair, reshaping large DataFrames on the Python backend using `pandas.melt()` is very expensive. It blocks the main thread, uses significant backend memory, and generates a massive JSON payload (6x larger for 6 variables) that has to be serialized and sent to the browser.
**Action:** Use Altair's `.transform_fold()` to push the reshaping operation to the Vega-Lite engine on the client side. This allows the backend to send the compact, wide DataFrame, drastically reducing CPU time, memory footprint, and network latency.

## 2026-03-02 - Streamlit Hashing Overhead for Large Uploaded Files
**Learning:** Passing a large `bytes` object (like `file.getvalue()`) directly as an argument to a `@st.cache_data` decorated function causes Streamlit to hash the entire payload on *every single app rerun* to check if the cache is still valid. For large files (e.g., 50MB+), this hashing overhead can take over a second, severely blocking the UI main thread during interactions.
**Action:** When caching operations on uploaded files, prefix the `bytes` argument with an underscore (e.g., `_file_content`) to instruct Streamlit to ignore it when generating the cache key. Instead, pass a lightweight, unique identifier like `file.file_id` as a regular argument to properly manage cache invalidation without the hashing overhead.

## 2026-03-04 - Matplotlib DPI Blocking Streamlit Main Thread
**Learning:** Hardcoding a very high DPI (e.g., `plt.rcParams['figure.dpi'] = 600`) for Matplotlib plots in a Streamlit app severely degrades performance. Rendering a high-DPI plot blocks the main thread (taking 5+ seconds for moderately sized datasets) and generates massive image payloads that must be serialized and sent to the client. This is especially problematic in Streamlit where user interactions often trigger full script reruns.
**Action:** Expose DPI as a user-configurable parameter in the UI with a sensible default (e.g., 100-150 DPI) for fast interactive exploration. Users can manually increase it only when they need a print-quality export.

## 2026-03-05 - Data Visualization Bottlenecks in Streamlit
**Learning:** Downsampling massive datasets simply for visualization is not a universally acceptable optimization. In some specific engineering contexts, plotting every data point might be desired, and downsampling logic might be seen as unexpected data modification or loss of fidelity, even if the raw data is technically untouched.
**Action:** Do not forcefully implement visualization downsampling on user datasets without explicit instruction.

## 2026-03-05 - Safe Matplotlib Caching in Streamlit
**Learning:** Matplotlib `Figure` objects are stateful and not thread-safe. Caching them directly using `@st.cache_resource` causes race conditions across user sessions. Caching them with `@st.cache_data` causes pickling errors. Additionally, hashing large DataFrame inputs to determine cache validity is extremely slow.
**Action:** To safely cache Matplotlib plots, render the figure to a `BytesIO` buffer, close the figure to prevent memory leaks, and return the PNG bytes. Cache this function with `@st.cache_data`. Use an underscore prefix for the DataFrame argument (e.g., `_data`) to bypass expensive hashing, and pass a lightweight identifier (e.g., `file_id`) to manage cache invalidation correctly. Finally, render the cached bytes using `st.image()` instead of `st.pyplot()`.
