## 2026-02-28 - Empty State Implementation
**Learning:** The Streamlit file uploader returns `None` or an empty list when no files are uploaded. This provides a natural branching point (`if files:` vs `else:`) to implement an empty state without complex state management.
**Action:** Always check if a file uploader or similar input has data before rendering the main UI, and provide an `st.info` or similar call-to-action when it's empty to guide the user.

## 2026-03-04 - User-Centric Labeling
**Learning:** Using technical implementation details (like "Altair", "Matplotlib", "Dataframe") for UI elements (like tab names) creates unnecessary cognitive load for users who only care about the functionality (e.g., interactive plotting, static plotting, viewing raw data).
**Action:** Always replace technical jargon with functional, user-centric language that clearly describes what the user can do or see, regardless of the underlying libraries used.
