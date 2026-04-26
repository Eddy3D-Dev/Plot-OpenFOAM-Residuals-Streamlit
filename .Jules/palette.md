## 2026-04-26 - Merge Altair Encodings for Cohesive Accessibility Legends
**Learning:** When using secondary visual encodings (like `strokeDash`) alongside `color` for colorblind accessibility in Altair, setting `legend=None` on the secondary encoding omits its pattern from the legend entirely. This prevents visually impaired users from mapping legend items to chart lines.
**Action:** To force Vega-Lite to merge the color and line style visual cues into a single cohesive legend, ensure both the `color` and `strokeDash` encodings share the exact same `legend` configuration (e.g., matching titles) and `sort` order. Never use `legend=None` for the secondary encoding.

## 2026-04-22 - Altair StrokeDash for Colorblind Accessibility
**Learning:** Relying solely on the `color` encoding in interactive Altair line charts makes them inaccessible to colorblind users. While Streamlit has settings to make static Matplotlib plots accessible via line styles, these are often not propagated to dynamic Altair charts.
**Action:** When building interactive Altair line charts in Streamlit, link a user-controlled accessibility toggle (like an `accessible_line_styles` checkbox) to dynamically add a `strokeDash` encoding (e.g., `strokeDash=alt.StrokeDash("Variable:N", legend=None)`) alongside `color`. This ensures colorblind users can distinguish series using patterns.

## 2024-05-18 - Use Toggles for Immediate Visual Preferences
**Learning:** For global settings that instantly toggle visual preferences (like grid lines, dark mode, or accessible line styles), users expect a "switch" interaction rather than a "checkbox" which implies submitting a form.
**Action:** Use `st.toggle` instead of `st.checkbox` for settings in the sidebar or globally that immediately update the UI without further confirmation.

## 2024-05-18 - Visual Hierarchy for Batch Actions
**Learning:** Overarching batch actions (like "Export all as .zip") easily get lost among individual file download buttons. Additionally, standard Streamlit buttons can have small click targets, violating Fitts's Law.
**Action:** Always apply `type="primary"` and `use_container_width=True` to batch action buttons (like `st.download_button` for zip files) to elevate their visual hierarchy and expand their click target, making them clearly distinct from individual item actions.

## 2024-05-18 - Artifact Prevention in Sparklines
**Learning:** When generating inline sparkline arrays for `st.metric` cards representing log-scaled data (like residuals), naively defaulting non-positive values to `0` (e.g. `[math.log10(v) if v > 0 else 0]`) creates massive, confusing visual spikes on the chart (since $10^0 = 1$), visually implying divergence rather than convergence.
**Action:** When preparing log-scaled sparkline data, explicitly filter out non-positive values (e.g. `[math.log10(v) for v in data if v > 0]`) to ensure the generated trendline accurately reflects the underlying data without artificial spikes.
