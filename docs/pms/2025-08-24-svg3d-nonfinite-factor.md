# svg3d shading failed on non-finite factor

- Date: 2025-08-24
- Author: codex
- Status: resolved

## Background
`svg3d._shade` scales RGB components by a caller-supplied factor. The function assumes the factor is a
finite float between 0 and 1.

## Root cause
The function multiplied RGB components by `factor` without verifying that the value was finite. When
`NaN` or `inf` reached `int()`, Python raised a `ValueError` and aborted execution.

## Detailed explanation
`_shade` underpins `draw_bar`, which renders bars in 3‑D heatmaps. Fuzzing introduced non‑finite
factors such as `float('nan')`. These values propagated through the multiplication step and failed
when cast to integers, crashing any script invoking the helper.

## Impact
Malformed input could crash scripts invoking `_shade` or `draw_bar`.

## Action items
### Prevent
- Validate shading factors with `math.isfinite` before computation.

### Detect
- Keep regression tests for non‑finite shading factors.

### Mitigate
- Raise a clear `ValueError` when encountering invalid factors.
