## 2026-05-02 - Contextual Icons for Comparison Views
**Learning:** In multi-file upload workflows or comparison views where repeated items (like charts or tables) are stacked vertically, using plain text headings for filenames makes scanning and distinguishing file types cognitively demanding.
**Action:** Dynamically inject format-specific Streamlit Material icons (e.g., `:material/article:` for `.log` files, `:material/description:` for `.dat` files) directly into repeated `st.subheader` strings. This creates a strong visual hierarchy, improves cognitive chunking, and allows users to quickly scan and differentiate file types at a glance.

## 2026-04-26 - Merge Altair Encodings for Cohesive Accessibility Legends
**Learning:** When using secondary visual encodings (like `strokeDash`) alongside `color` for colorblind accessibility in Altair, setting `legend=None` on the secondary encoding omits its pattern from the legend entirely. This prevents visually impaired users from mapping legend items to chart lines.
**Action:** To force Vega-Lite to merge the color and line style visual cues into a single cohesive legend, ensure both the `color` and `strokeDash` encodings share the exact same `legend` configuration (e.g., matching titles) and `sort` order. Never use `legend=None` for the secondary encoding.

## 2026-04-22 - Altair StrokeDash for Colorblind Accessibility
**Learning:** Relying solely on the `color` encoding in interactive Altair line charts makes them inaccessible to colorblind users. While Streamlit has settings to make static Matplotlib plots accessible via line styles, these are often not propagated to dynamic Altair charts.
**Action:** When building interactive Altair line charts in Streamlit, link a user-controlled accessibility toggle (like an `accessible_line_styles` checkbox) to dynamically add a `strokeDash` encoding alongside `color`. To force Vega-Lite to merge the color and line style visual cues into a single, cohesive legend, ensure both the `color` and `strokeDash` encodings share the exact same `legend` configuration (e.g., matching titles) and `sort` order. Never use `legend=None` for the secondary encoding, as it will omit those cues from the legend entirely.

## 2024-05-18 - Use Toggles for Immediate Visual Preferences
**Learning:** For global settings that instantly toggle visual preferences (like grid lines, dark mode, or accessible line styles), users expect a "switch" interaction rather than a "checkbox" which implies submitting a form.
**Action:** Use `st.toggle` instead of `st.checkbox` for settings in the sidebar or globally that immediately update the UI without further confirmation.

## 2024-05-18 - Visual Hierarchy for Batch Actions
**Learning:** Overarching batch actions (like "Export all as .zip") easily get lost among individual file download buttons. Additionally, standard Streamlit buttons can have small click targets, violating Fitts's Law.
**Action:** Always apply `type="primary"` and `use_container_width=True` to batch action buttons (like `st.download_button` for zip files) to elevate their visual hierarchy and expand their click target, making them clearly distinct from individual item actions.

## 2024-05-18 - Artifact Prevention in Sparklines
**Learning:** When generating inline sparkline arrays for `st.metric` cards representing log-scaled data (like residuals), naively defaulting non-positive values to `0` (e.g. `[math.log10(v) if v > 0 else 0]`) creates massive, confusing visual spikes on the chart (since $10^0 = 1$), visually implying divergence rather than convergence.
**Action:** When preparing log-scaled sparkline data, explicitly filter out non-positive values (e.g. `[math.log10(v) for v in data if v > 0]`) to ensure the generated trendline accurately reflects the underlying data without artificial spikes.

## 2024-05-19 - Merging Multiple Encodings into One Altair Legend
**Learning:** When making an interactive Altair chart accessible with secondary encodings (like `strokeDash` alongside `color`), providing `legend=None` to the secondary encoding completely omits those visual cues from the legend. This leaves colorblind users unable to map the line styles to their respective variables.
**Action:** To force Vega-Lite to merge multiple encodings (e.g., color and line style) into a single, fully accessible legend, ensure that both encodings share the exact same `legend` configuration (e.g., matching titles) and the exact same `sort` order.

## 2026-04-28 - Colorblind Safe Palettes in Streamlit Charts
**Learning:** While combining line styles with colors improves accessibility in charts, the default categorical color palettes (like `category10` in Vega-Lite or `default` in Matplotlib) are not fully colorblind safe. This can still make distinguishing between variables difficult even with different dash patterns.
**Action:** When implementing an accessibility toggle for charts, actively switch the color scales to colorblind-safe schemes (like `scheme="dark2"` for Altair and `plt.style.context("tableau-colorblind10")` for Matplotlib) in addition to applying varying line styles. This provides robust multi-channel differentiation.

## 2026-04-30 - Cognitive Chunking in Configuration Sidebars
**Learning:** When sidebars accumulate multiple independent settings (e.g., plot dimensions alongside accessibility toggles), presenting them as a flat list increases cognitive load and degrades discoverability.
**Action:** Use `st.markdown("#### Category Name")` and `st.divider()` in Streamlit to create semantic groups (cognitive chunking). This visual hierarchy helps users quickly locate specific classes of settings without scanning the entire list.

## 2026-04-30 - Material Icons for Consistent Scannability in Headings
**Learning:** Using OS-dependent emojis (like ⚙️) or plain text for semantic headers creates inconsistent visual experiences across platforms and breaks visual harmony with components that natively support Streamlit Material icons (like buttons, tabs, or toasts).
**Action:** Always prefer embedding Streamlit Material Design icon syntax (e.g., `:material/settings:`) directly into markdown headings (`st.markdown("#### :material/icon: Title")` or `st.header(":material/icon: Title")`) to establish a consistent, polished visual hierarchy and improve cognitive chunking and scannability.

## 2026-05-03 - Consistent Sidebar Layouts without DuplicateWidgetID Exceptions
**Learning:** Attempting to pre-render a "disabled" UI control (like `st.toggle`) in a placeholder and then overwriting it *later in the same script execution* causes a fatal `DuplicateWidgetID` error in Streamlit, because Streamlit registers both widget calls even if they target the same `st.empty()`.
**Action:** To prevent layout shifts for controls that depend on parsed data while avoiding duplicate widget errors, inspect the input data *before* rendering the sidebar. This allows you to render the control statically exactly once (with the correct active/disabled state computed upfront) within its semantic group, ensuring visual chunking and layout stability without brittle placeholder overwriting.

## 2026-05-06 - Explicit Scientific Notation for Log-Scaled Engineering Axes
**Learning:** When visualizing small engineering values (like CFD residuals) on a log-scaled axis in Altair/Vega-Lite, the default axis formatting often fails to render very small numbers legibly, either dropping them to `0` or creating extremely long decimals that clip text.
**Action:** Always explicitly specify scientific notation for the axis formatting (e.g., `axis=alt.Axis(format="e")`) when dealing with small, log-scaled engineering variables. This aligns with domain conventions, maintains precise scaling visibility, and prevents text clipping in the UI.
## 2025-05-08 - [Altair Quantitative Axes Default to Zero]
**Learning:** By default, Altair (Vega-Lite) quantitative axes (`:Q`) include `0`, which can severely compress data when visualizing time series or offset values (e.g., iterations starting at 10,000).
**Action:** Use `scale=alt.Scale(zero=False)` explicitly when plotting quantitative offset data like iterations, times, or dates that are far from zero to ensure the data fills the chart area optimally.

## 2026-05-10 - Unidirectional Zooming for Time-Series Logs
**Learning:** When users interact with a time-series chart (or convergence plot) that uses a log-scaled Y-axis, allowing default two-dimensional zooming (both X and Y axes) is highly disorienting. Zooming on a log-scaled Y-axis distorts the relative magnitude of values and quickly leads to users getting "lost" in the plot.
**Action:** When enabling interactivity (panning/zooming) on Altair charts where the Y-axis represents magnitude or uses a log scale over time/iterations, restrict the interactivity solely to the X-axis using `chart.interactive(bind_y=False)`. This preserves the vertical scale perspective while allowing users to scrub through the time domain.

## 2026-05-15 - Expose Hidden Interactivity in Legends
**Learning:** Native visualization capabilities like Altair/Vega-Lite's `shift-click` multi-select functionality in interactive legends are completely invisible by default. This makes the feature undiscoverable for sighted users and inaccessible for screen reader users unless explicitly documented in the UI.
**Action:** When enabling interactive selections (e.g. `bind='legend'`) in charts, explicitly append instructions for advanced modifier key interactions directly into the legend title (e.g., `title="Variable (click to isolate, shift-click for multiple)"`) and the chart's ARIA `description` to ensure the interaction is discoverable and accessible to all users.

## 2026-05-18 - Wrapping Lines in Code Blocks for Scannability
**Learning:** When displaying long text lines (such as OpenFOAM log file lines or Python tracebacks) inside code blocks (`st.code`), the default horizontal scrolling makes the text extremely difficult to read and breaks the flow of scanning the UI.
**Action:** Always enable line wrapping (`wrap_lines=True`) in `st.code` blocks when displaying content that is expected to have long lines (like log file examples or error tracebacks) to improve scannability and ensure users can see the full context without tedious horizontal scrolling.
