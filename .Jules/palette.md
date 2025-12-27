# Palette's Journal

## 2024-05-22 - [Visualization]
**Learning:** Porkchop plots are traditionally dense with contour lines, making them hard to read without filled colors.
**Action:** Use `contourf` with a perceptually uniform colormap (like 'viridis') and a colorbar for better readability.

## 2024-10-18 - [CLI Feedback]
**Learning:** Long-running CLI processes (like trajectory optimization) feel broken without feedback. A simple text progress bar significantly improves confidence.
**Action:** Implement optional `verbose` modes with text-based progress bars for computationally intensive loops.

## 2024-10-24 - [CLI Summary]
**Learning:** Users running optimization tools primarily want the "answer" (best value) immediately, rather than digging through generated artifacts.
**Action:** Always calculate and display key summary metrics (like optimal Min/Max values) directly in the CLI output after processing.
