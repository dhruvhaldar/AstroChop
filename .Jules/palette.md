## 2024-05-22 - [CLI Progress Indicators]
**Learning:** Users running long-duration compute tasks (like orbital mechanics) feel significantly more confident when provided with an ETA (Estimated Time of Arrival) in the progress bar.
**Action:** When implementing CLI loops that take more than a few seconds, always include an ETA calculation using `time.time()` differences.
