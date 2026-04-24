## 2026-04-22 - Altair StrokeDash for Colorblind Accessibility
**Learning:** Relying solely on the `color` encoding in interactive Altair line charts makes them inaccessible to colorblind users. While Streamlit has settings to make static Matplotlib plots accessible via line styles, these are often not propagated to dynamic Altair charts.
**Action:** When building interactive Altair line charts in Streamlit, link a user-controlled accessibility toggle (like an `accessible_line_styles` checkbox) to dynamically add a `strokeDash` encoding (e.g., `strokeDash=alt.StrokeDash("Variable:N", legend=None)`) alongside `color`. This ensures colorblind users can distinguish series using patterns.

## 2024-05-18 - Use Toggles for Immediate Visual Preferences
**Learning:** For global settings that instantly toggle visual preferences (like grid lines, dark mode, or accessible line styles), users expect a "switch" interaction rather than a "checkbox" which implies submitting a form.
**Action:** Use `st.toggle` instead of `st.checkbox` for settings in the sidebar or globally that immediately update the UI without further confirmation.
