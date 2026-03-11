## 2026-02-28 - Empty State Implementation
**Learning:** The Streamlit file uploader returns `None` or an empty list when no files are uploaded. This provides a natural branching point (`if files:` vs `else:`) to implement an empty state without complex state management.
**Action:** Always check if a file uploader or similar input has data before rendering the main UI, and provide an `st.info` or similar call-to-action when it's empty to guide the user.

## 2026-03-04 - User-Centric Labeling
**Learning:** Using technical implementation details (like "Altair", "Matplotlib", "Dataframe") for UI elements (like tab names) creates unnecessary cognitive load for users who only care about the functionality (e.g., interactive plotting, static plotting, viewing raw data).
**Action:** Always replace technical jargon with functional, user-centric language that clearly describes what the user can do or see, regardless of the underlying libraries used.
## 2024-03-05 - Graceful Error States for File Uploads
**Learning:** In Streamlit applications, failing to catch parsing errors on file uploads causes a stack trace that blocks the entire UI.
**Action:** Always wrap file upload processing logic in `try...except` blocks and use `st.error` to provide actionable feedback instead of crashing. Accompany this with `st.spinner` to provide loading feedback.

## 2026-03-05 - Ephemeral Notifications
**Learning:** Streamlit UI interactions (like toggling a checkbox) rerun the entire script. If a notification like `st.toast` or `st.balloons` is placed conditionally inside a block that runs (like checking if files are uploaded), it will fire on *every* interaction, creating an annoying experience.
**Action:** Always guard ephemeral UI notifications using `st.session_state` to track the specific items (e.g., file IDs) that triggered them, ensuring the notification only appears for *new* events.

## 2026-03-05 - Responsive Dataframes
**Learning:** By default, Streamlit's `st.dataframe` does not expand to the full container width, often leading to cramped tables and awkward white space that doesn't align with full-width charts above them.
**Action:** Use `st.dataframe(data, use_container_width=True)` to ensure tables fill the available horizontal space, improving readability and layout consistency.

## 2026-03-05 - Interactive Legends in Dense Plots
**Learning:** For line charts with multiple series (like plotting various OpenFOAM residuals), static plots often become visually overwhelming and unreadable as lines overlap.
**Action:** Always enhance UX by implementing interactive legends using `alt.selection_point(bind='legend')` with conditional opacity. This allows users to isolate specific variables dynamically without the need for additional UI controls like checkboxes, reducing visual clutter.

## 2026-03-05 - Dynamic Variable Parsing
**Learning:** Hardcoding expected variables (e.g., `['Ux', 'Uy', 'Uz', 'p', 'epsilon', 'k']`) when creating plots in Streamlit using Altair's `.transform_fold()` leads to silent data omission if the user uploads a dataset with different variables (like `omega` or `nuTilda`), which degrades trust and usability.
**Action:** Always use dynamic column references (e.g., `list(data.columns)`) when transforming and plotting user-uploaded datasets to ensure all variables are robustly parsed and displayed, accommodating diverse user data.

## 2026-03-11 - Export Options for Generated Content
**Learning:** For web applications that generate visual content (like high-quality static Matplotlib plots), users naturally expect to be able to save them. Relying entirely on browser functionality like "Right Click -> Save Image As" is undiscoverable and often provides a poor user experience, especially if the underlying image is displayed differently (e.g., within an `st.image` wrapper that might alter its natural behavior).
**Action:** Always provide explicit, discoverable export options (like `st.download_button`) below generated visualizations, ensuring the downloaded file has a meaningful, pre-populated filename (e.g., incorporating the original uploaded filename).
