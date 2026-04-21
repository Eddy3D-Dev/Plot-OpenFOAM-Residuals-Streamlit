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

## 2024-03-05 - Grid Lines for Log-Scale Plots
**Learning:** Static log-scale plots (like OpenFOAM residuals) are notoriously difficult to read without grid lines, as users struggle to trace data points back to the axis across large empty spaces.
**Action:** Always include subtle grid lines (`ax.grid(True, which="both", alpha=0.5)`) on generated static plots, especially those using logarithmic scales, to significantly improve visual accessibility and data tracking.

## 2026-03-13 - Contextual Disabled States and Tooltips
**Learning:** Using progressive disclosure and conditionally disabling sidebar inputs until prerequisite data (like an uploaded file) is provided significantly improves UX. Users aren't left guessing why changing a setting has no effect, especially when paired with a contextual tooltip explaining *why* the input is disabled.
**Action:** Always conditionally disable input controls that depend on uploaded data, and replace the standard `help` text with a clear, actionable explanation (e.g., "⚠️ Please upload a residual file first to enable this setting.") while the input is in a disabled state.

## 2026-03-14 - Data Summarization & Formatting in Tables
**Learning:** Presenting a raw, massive dataset (like OpenFOAM residuals) directly in a table is overwhelming and unhelpful for the user's primary goal, which is usually assessing the final convergence state. Users are forced to scroll past thousands of rows to find the only information they care about. Additionally, raw floating-point numbers often display poorly without consistent formatting.
**Action:** Always provide a high-level summary (e.g., using `st.metric` cards) of the most important data points (like the final iteration values) *above* the raw data table. Furthermore, use tools like `st.column_config` to enforce consistent, readable formatting (e.g., scientific notation `%.4e` for residuals) across the entire dataframe to improve scannability and professional polish.

## 2024-03-24 - Responsive Grid Wrapping for Dynamic Content
**Learning:** Generating dynamic horizontal columns (like `st.columns(len(data.columns))`) without a maximum width constraint creates severe layout problems when user data contains many items. In Streamlit, this causes text inside components like `st.metric` to become horizontally squished and truncated (e.g., "1.23..."), rendering the data unreadable.
**Action:** Always implement explicit wrapping for dynamically generated grid layouts. Group items into chunks with a sane maximum (e.g., 4 columns per row) to ensure consistent readability regardless of how many variables the user provides.

## 2026-03-24 - Contextualizing Isolated Numbers via Baselines
**Learning:** Displaying raw final values (e.g., in `st.metric`) lacks context for users trying to assess convergence progress, as they have to manually mentally compare the final value to their initial expectations.
**Action:** Always provide context for isolated numbers by using features like `delta` in `st.metric` to explicitly show the relative change (e.g., order of magnitude drop) from a sensible baseline (like the first iteration). Add a `help` tooltip to ensure the baseline metric is clearly understood by the user.

## 2026-03-24 - Enhancing Empty States and Error Messages
**Learning:** Dead-end empty states and generic error messages provide poor user experiences. Users don't know what format to use for file uploads, and when errors occur, generic messages don't help them self-correct.
**Action:** Always enhance empty states by showing explicit examples (e.g., using `st.code`) of expected file formats. For error notifications, always surface raw exception traces inside an `st.expander` to help users understand what went wrong without cluttering the main UI.

## 2026-03-26 - Action Discoverability with Icons
**Learning:** Text-only buttons for common primary actions (like downloading a CSV or exporting an image zip) blend into the UI, requiring users to read every button's text to find their desired action. This increases cognitive load and reduces discoverability.
**Action:** Always pair prominent calls to action (like `st.download_button`) with contextually relevant, universally understood Material icons (e.g., `:material/download:` or `:material/folder_zip:`) to enhance scannability and create a more intuitive, accessible user experience.

## 2026-03-27 - Removing Redundant Table Indices
**Learning:** When displaying Pandas DataFrames in Streamlit via `st.dataframe`, Streamlit automatically renders the dataframe's index as the first column. If the dataframe was previously reset (`data.reset_index()`), this results in a redundant, meaningless numerical column (0, 1, 2...) that clutters the UI and distracts from the actual user data.
**Action:** Always use `hide_index=True` in `st.dataframe` when displaying dataframes that either lack a meaningful index or have had their meaningful index explicitly converted to a standard column, ensuring a clean and focused data presentation.

## 2026-04-04 - Add unit formatting to Streamlit sliders
**Learning:** Adding explicit units (e.g., `%d px`) directly to Streamlit `st.slider` widgets via the `format` parameter significantly improves clarity at a glance, reducing the need for users to read help tooltips to understand the unit of measurement.
**Action:** When adding or updating Streamlit sliders that represent physical units (pixels, percentages, degrees), always use the `format` parameter to append the unit directly to the displayed value.

## 2026-04-04 - Consistent Terminology Across UI Views
**Learning:** When displaying the same underlying data attribute across different views (e.g., a chart's X-axis labeled 'Iterations' vs a data table's column labeled 'Time'), using inconsistent labels creates cognitive friction for the user trying to map the visual representation to the raw data.
**Action:** Always ensure column headers in data tables (`st.column_config`) align perfectly with the axis titles used in corresponding charts to provide a cohesive, unified terminology across the entire application interface.

## 2026-04-04 - Sample File Downloads in Empty States
**Learning:** For file-upload dependent web applications, presenting an empty state without data acts as a hard barrier. Even if the expected format is documented, users must find or generate compatible files before they can evaluate the application's utility. Providing a downloadable sample file directly within the empty state significantly reduces this friction and improves onboarding.
**Action:** Always include a clearly labeled, one-click `st.download_button` providing a minimal, valid sample file within empty states for upload-driven applications.

## 2026-03-31 - Visual Grouping for Repeated Content Blocks
**Learning:** When displaying complex repeated content blocks (like charts and data tables for multiple uploaded files) in a sequential layout, users can easily lose track of which block belongs to which file, leading to ambiguous action associations (e.g., clicking the wrong download button).
**Action:** Always use clear visual separators (like `st.divider()`) between repeated complex UI blocks to create distinct boundaries and group related content together, significantly reducing cognitive load and preventing misclicks.

## 2024-04-01 - Contextual Export Actions
**Learning:** When users see an image or visual chart, they expect the download button immediately beneath it to export that visual asset, not the raw underlying data. Redundant raw data downloads (especially if available elsewhere, like a Data tab) create a mismatch between user expectation and the button's action.
**Action:** Always ensure export buttons are contextually relevant to the content immediately preceding them (e.g., placing an "Export Image" button below a chart, rather than a generic "Download CSV" button).
## 2025-04-02 - Embellishing Streamlit Tabs
**Learning:** Streamlit `st.tabs` does not currently support an `icon=` keyword argument, unlike other UI components.
**Action:** When embellishing `st.tabs` for scannability, use the native `:material/icon_name:` syntax directly within the tab title string (e.g., `st.tabs([":material/show_chart: Tab 1", ":material/image: Tab 2"])`) to add small touches of visual delight.

## 2024-04-04 - Aligning download actions with visual context
**Learning:** Download buttons placed directly beneath visual charts create an expectation of downloading an image. Placing raw data (CSV) downloads in these locations causes a mismatch between user expectation and the button's action.
**Action:** Remove raw data download buttons from beneath visual charts. Ensure that download buttons beneath charts only export images, and that raw data downloads are placed in a dedicated "Raw Data" or similar tab. Add descriptive `help` tooltips to clarify the specific action of each download button.

## 2026-04-04 - Demo Buttons in Empty States
**Learning:** For file-upload dependent web applications, providing a sample file download in the empty state is helpful, but still requires the user to manually upload it. Adding an explicit "Load sample data" button that automatically populates the application with sample data removes all friction and instantly demonstrates the application's value proposition without making the user leave the page.
**Action:** In addition to providing sample file downloads, always add a primary "Load sample data" (or "Load Demo Data") button in the empty states of upload-driven applications. Manage this via `st.session_state` so the demo data is instantly cleared once a real file is uploaded, and provide a clear way for the user to manually exit the demo view.
## 2026-04-06 - Enhance Streamlit Alert and Expander Scannability
**Learning:** Users often overlook standard Streamlit expanders and informational alerts when scanning dense data dashboards. Adding contextually relevant Material icons to `st.expander`, `st.warning`, and `st.info` significantly improves visual hierarchy and helps users quickly locate secondary information (like FAQs or error details) and understand the severity/context of messages.
**Action:** Always include the `icon` parameter (e.g., `icon=":material/help:"`) when using `st.expander`, `st.info`, `st.warning`, or `st.error` in Streamlit applications to provide immediate visual context.

## 2026-04-06 - Empty State Button Styling
**Learning:** In empty states containing multiple side-by-side buttons (e.g., "Load demo data" vs. "Download sample file" in columns), using default Streamlit button styling causes the buttons to have different widths depending on their text, looking messy. Furthermore, lacking a visual hierarchy makes it unclear which action is preferred.
**Action:** Always add `type="primary"` to the most frictionless onboarding action to guide the user. Additionally, set `use_container_width=True` on all buttons in empty-state row layouts so they align uniformly and provide larger, more accessible click targets.

## 2026-04-06 - Grouping Global Controls
**Learning:** Placing layout toggles (like "Show filenames") directly inside the main content area creates visual fragmentation and dynamically pushes the main tabbed content down when they appear. This disrupts the reading flow and separates related controls.
**Action:** Always group global display controls logically within dedicated sections (like `st.sidebar` under a "Settings" header). Use tools like `st.empty()` placeholders to inject controls into these sections even if they depend on data loaded later in the main script.

## 2024-04-06 - Conditional Batch Actions for Redundancy Reduction
**Learning:** Batch actions like "Export all as zip" are extremely useful for users working with multiple files, saving them repetitive clicks. However, rendering a batch "Export all" button when only one file is present in the view is redundant and confusing, creating a mismatch between UI options and actual data state.
**Action:** Always wrap batch actions (like zipping multiple images or CSVs) in a conditional check (e.g., `if len(items) > 1:`) so they only render when they provide actual value, keeping the UI clean and relevant. Additionally, ensure these batch actions are available consistently across all applicable tabs (e.g., both static images and raw data tables) to provide a cohesive experience.

## 2026-04-12 - Verifying Altair ARIA Labels with Playwright
**Learning:** When using Playwright to verify the `aria-label` of an Altair/Vega-Lite chart in Streamlit, the attribute is applied to the inner `<div role="graphics-document">` element inside the `[data-testid="stVegaLiteChart"]` container, not on a `<figure>` tag.
**Action:** Extract the inner HTML of the chart container and use regex or specific locators targeting `role="graphics-document"` to verify `aria-label` attributes for Altair charts in Streamlit.

## 2026-04-06 - Accessible Data Visualizations
**Learning:** Data visualizations like Altair/Vega-Lite charts are inherently opaque to screen readers by default. Without an explicit description, visually impaired users cannot understand what the chart represents or what data it contains.
**Action:** Always provide a clear, descriptive `aria-label` equivalent for charts. In Altair, use `.properties(description="...")` to inject a dynamic description string that explains the chart's purpose and the data it visualizes.

## 2026-04-13 - Comprehensive Empty State Examples
**Learning:** When an application supports multiple distinct file formats, showing an example for only one format leaves users guessing about the others. Providing a massive text block with examples for all formats is cluttered.
**Action:** When a Streamlit application accepts multiple file formats, enhance the empty state by using `st.tabs` to neatly organize and present explicit format examples (e.g., via `st.code`) for each supported type, ensuring comprehensive guidance without UI clutter.
## 2024-05-14 - Altair Interactive Legend Discoverability
**Learning:** Altair line charts with `bind="legend"` selections offer powerful interactivity (isolating lines), but this functionality is completely invisible to users by default. Without a visual cue, users rarely discover they can click the legend.
**Action:** Always append a brief, actionable hint (e.g., `legend=alt.Legend(title="Variable (click to isolate)")`) to the legend title when binding selections to it in Altair/Streamlit.

## 2026-04-15 - Enhancing single-value metrics with sparklines and borders
**Learning:** Displaying standalone final values (e.g., using `st.metric`) is useful, but often lacks visual context regarding how the value was reached. While the `delta` parameter shows the total change, adding a sparkline via `chart_data` (especially with log-scaled values for data that changes by orders of magnitude) provides an immediate, intuitive visual history of the data's progression without requiring a full chart. Furthermore, applying `border=True` neatly bounds the metric and its accompanying sparkline, establishing a clear visual hierarchy and preventing the UI from looking disorganized.
**Action:** Always consider adding `chart_data` to `st.metric` when visualizing single values derived from time-series or sequential data to provide inline visual context. Ensure the data passed to `chart_data` is appropriately scaled (e.g., log10 for exponential decay) so the sparkline is informative, and use `border=True` to neatly containerize the component.

## 2026-04-18 - Semantic Headers and Contextual Column Tooltips
**Learning:** Using non-semantic markdown formatting (like `**Bold Text**`) to simulate headers prevents screen readers from understanding the document structure, harming accessibility. Additionally, presenting raw variable names as column headers without explanation leaves users guessing their meaning.
**Action:** Always use semantic markdown headers (like `#### Heading`) to establish proper document hierarchy for assistive technologies. Furthermore, actively use features like the `help` parameter in `st.column_config` to attach descriptive tooltips directly to data table headers, providing necessary context without cluttering the UI.

## 2026-04-18 - Colorblind-Accessible Data Visualizations
**Learning:** Relying solely on color to differentiate multiple series in a static plot (like Matplotlib) makes the chart unreadable for colorblind users and useless when printed in black-and-white.
**Action:** Always combine color with a secondary visual channel, such as line styles (`["-", "--", "-.", ":"]` or different markers), to ensure data series remain distinguishable regardless of color perception or medium.

## 2026-04-19 - Accessible Static Plots
**Learning:** Streamlit's `st.pyplot()` function natively renders Matplotlib figures as images but lacks any mechanism to provide `alt` text or captions, rendering the plots completely opaque to screen readers.
**Action:** When rendering static Matplotlib figures, convert the figure to PNG bytes and display it using `st.image(..., caption="...")` instead of `st.pyplot()`. This provides a descriptive text equivalent for visually impaired users. Remember to manually close the Matplotlib figure (`plt.close(fig)`) since `st.pyplot(..., clear_figure=True)` is no longer handling it.
