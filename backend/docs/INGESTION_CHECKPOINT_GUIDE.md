# Ingestion Checkpoint System

**Created**: January 2, 2026  
**Purpose**: Enable resume functionality for data ingestion pipeline to save time and resources

## Overview

The checkpoint system allows the ingestion pipeline to save its state after each major step and resume from the last completed step in case of crashes, interruptions, or when iterating on specific steps during development.

## Benefits

- **Time Savings**: Skip completed steps (Steps 1-2 take ~2-3 minutes)
- **Development Speed**: Faster iteration when debugging specific steps
- **Crash Recovery**: Automatic resume after crashes
- **Resource Efficiency**: Don't re-fetch data from Socrata unnecessarily
- **Cost Savings**: Reduce API calls to external services

## Usage

### Basic Commands

```bash
# Normal ingestion (will auto-resume if checkpoint exists)
python ingest_data_cnn_segments.py --resume

# Force full restart (ignore checkpoint)
python ingest_data_cnn_segments.py --force-restart

# Resume from specific step
python ingest_data_cnn_segments.py --resume-from=3

# Show checkpoint info
python ingest_data_cnn_segments.py --checkpoint-info

# Clear checkpoint
python ingest_data_cnn_segments.py --clear-checkpoint
```

### Programmatic Usage

```python
from ingestion_checkpoint import CheckpointManager

# Initialize
checkpoint = CheckpointManager()

# Save checkpoint after completing a step
checkpoint.save(
    step="2.5",
    all_segments=segments,
    streets_metadata=metadata,
    stats={"segments_created": 34324}
)

# Load checkpoint at start
data = checkpoint.load()
if data:
    segments = data['all_segments']
    metadata = data['streets_metadata']
    start_from = data['next_step']
    print(f"Resuming from Step {start_from}")
```

## Step Order

The system recognizes these steps in order:

1. **Step 1**: Create CNN segments
2. **Step 2**: Add blockface geometries
3. **Step 2.5**: Generate synthetic blockfaces
4. **Step 3**: Match parking regulations
5. **Step 4**: Match meters
6. **Step 5**: Match street sweeping
7. **Step 5.4**: Apply manual overrides
8. **Step 5.5**: Finalize segments
9. **Step 5.6**: Aggregate meter rules
10. **Step 5.7**: Finalize cardinal direction
11. **Step 6**: Save to database

## Checkpoint Files

The system creates two files:

1. **`.ingestion_checkpoint.json.gz`**: Metadata (small, JSON)
   - Last completed step
   - Next step to run
   - Timestamp
   - Statistics

2. **`.ingestion_checkpoint_data.pkl.gz`**: Data (large, pickle)
   - All segments array
   - Streets metadata dictionary

Both files are gzip-compressed to save disk space.

## When to Use Full Restart

Use `--force-restart` when:

- **Schema changes** in early steps
- **New fields** added to segments
- **Data model updates**
- **Suspected data corruption**
- **Testing from scratch**

## When to Use Resume

Use `--resume` when:

- **Crash recovery** after Step 3 or later
- **Debugging** specific steps
- **Iterating** on later steps (5.4-6)
- **Network interruptions** during ingestion

## Example Scenarios

### Scenario 1: Crash During Step 3

```bash
# Ingestion crashes at Step 3 (64% complete)
# Steps 1, 2, 2.5 already completed

# Resume automatically
python ingest_data_cnn_segments.py --resume

# Output:
# ✓ Checkpoint found: Last completed Step 2.5
#   Timestamp: 2026-01-02T01:30:00Z
#   Segments: 34324
#   Next step: 3
# Skipping Steps 1, 2, 2.5...
# === STEP 3: Matching Parking Regulations ===
```

### Scenario 2: Debugging Step 5.4

```bash
# You're working on manual overrides logic
# Don't want to re-run Steps 1-5 every time

# Resume from Step 5.4
python ingest_data_cnn_segments.py --resume-from=5.4

# Make changes to apply_manual_overrides.py
# Run again
python ingest_data_cnn_segments.py --resume-from=5.4
```

### Scenario 3: Schema Change

```bash
# You added a new field to segments in Step 1
# Need to regenerate everything

# Force full restart
python ingest_data_cnn_segments.py --force-restart
```

## Implementation Details

### Data Storage

- **Compression**: gzip reduces file size by ~80%
- **Format**: JSON for metadata, pickle for data
- **Location**: Current directory (`.ingestion_checkpoint.*`)

### Safety

- **Validation**: Checks file existence before loading
- **Error Handling**: Falls back to fresh start if checkpoint corrupt
- **Atomic Writes**: Uses temp files to prevent corruption

### Performance

- **Save Time**: ~1-2 seconds (gzip compression)
- **Load Time**: ~2-3 seconds (gzip decompression)
- **Disk Space**: ~50-100 MB compressed (vs ~500 MB uncompressed)

## Integration with Existing Code

The checkpoint system is designed to integrate seamlessly:

```python
async def main():
    # Add argument parsing
    import argparse
    from ingestion_checkpoint import CheckpointManager, add_checkpoint_args
    
    parser = argparse.ArgumentParser()
    add_checkpoint_args(parser)
    args = parser.parse_args()
    
    checkpoint = CheckpointManager()
    
    # Handle checkpoint commands
    if args.clear_checkpoint:
        checkpoint.clear()
        return
    
    if args.checkpoint_info:
        info = checkpoint.get_info()
        print(json.dumps(info, indent=2))
        return
    
    # Load checkpoint if resuming
    start_step = "1"
    all_segments = []
    streets_metadata = {}
    
    if args.resume and not args.force_restart:
        data = checkpoint.load()
        if data:
            all_segments = data['all_segments']
            streets_metadata = data['streets_metadata']
            start_step = data['next_step']
    
    # Run steps conditionally
    if checkpoint.should_resume_from("1"):
        # Step 1...
        checkpoint.save("1", all_segments, streets_metadata)
    
    if checkpoint.should_resume_from("2"):
        # Step 2...
        checkpoint.save("2", all_segments, streets_metadata)
    
    # etc.
```

## Future Enhancements

Potential improvements:

1. **Incremental Updates**: Only re-process changed data
2. **Parallel Processing**: Checkpoint per-district for parallel execution
3. **Cloud Storage**: Save checkpoints to S3/GCS for distributed systems
4. **Versioning**: Track schema version in checkpoint
5. **Metrics**: Track time saved by resuming

## Troubleshooting

### Checkpoint Won't Load

```bash
# Clear and restart
python ingest_data_cnn_segments.py --clear-checkpoint --force-restart
```

### Wrong Step Resumed

```bash
# Specify exact step
python ingest_data_cnn_segments.py --resume-from=3
```

### Disk Space Issues

```bash
# Checkpoints use ~50-100 MB
# Clear old checkpoints
python ingest_data_cnn_segments.py --clear-checkpoint
```

## References

- Implementation: [`ingestion_checkpoint.py`](ingestion_checkpoint.py)
- Main Ingestion: [`ingest_data_cnn_segments.py`](ingest_data_cnn_segments.py)
- Architecture: [`CNN_MASTER_REFERENCE_ARCHITECTURE.md`](CNN_MASTER_REFERENCE_ARCHITECTURE.md)

---

**Last Updated**: January 2, 2026