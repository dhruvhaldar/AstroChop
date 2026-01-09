# Palette's Journal

## 2024-05-22 - [Visualization]
**Learning:** Porkchop plots are traditionally dense with contour lines, making them hard to read without filled colors.
**Action:** Use `contourf` with a perceptually uniform colormap (like 'viridis') and a colorbar for better readability.

## 2024-10-18 - [CLI Feedback]
**Learning:** Long-running CLI processes (like trajectory optimization) feel broken without feedback. A simple text progress bar significantly improves confidence.
**Action:** Implement optional `verbose` modes with text-based progress bars for computationally intensive loops.

## 2024-11-20 - [Data Visualization]
**Learning:** For optimization problems, users struggle to map numerical best-values from the console to the visual heatmap.
**Action:** Always explicitly mark the global optimum (e.g., with a star ⭐️) on the generated plot to bridge the gap between data and visualization.

## 2024-05-20 - [Artifact Usability]
**Learning:** Generated artifacts (like images) often get separated from the CLI log that produced them, losing context.
**Action:** Embed critical optimization results (like min value) directly into the artifact title so it is self-describing and useful standalone.

## 2024-05-24 - [Scientific Visualization]
**Learning:** In scientific plots, missing units in annotations forces users to look up context elsewhere or guess.
**Action:** Always include units (e.g., `km/s`, `days`) directly in data annotations to make the artifact self-contained and unambiguous.

## 2024-12-14 - [Cognitive Load]
**Learning:** Users often perform mental math to convert between related metrics (e.g., Energy vs. Delta-V).
**Action:** Explicitly display derived metrics (like Dep $V_\infty$ alongside $C_3$) in summary views to reduce cognitive load and bridge different mental models.
