# API Performance Benchmarks

## Tracking Log

### 2025-11-29 - Initial Optimization Baseline
**Context:** Post-optimization of `api/v1/blockfaces` endpoint.
**Environment:** Local Development (macOS)

| Test Case | Radius (m) | Items Returned | Avg Time (s) | Status |
|-----------|------------|----------------|--------------|--------|
| Small     | 300        | 74             | 0.0879       | OK     |
| Medium    | 1000       | 950            | 0.6143       | OK     |
| Large     | 2600       | 7482           | 3.7180       | OK     |

**Notes:**
- Small queries (<100 items) are sub-100ms, which is excellent for UI responsiveness.
- Medium queries (~1000 items) are ~600ms, providing good UX for zooming out.
- Large queries (~7500 items) take ~3.7s, which is acceptable for bulk data loading but could be improved with further optimization (e.g., tiling, simplification) if needed.