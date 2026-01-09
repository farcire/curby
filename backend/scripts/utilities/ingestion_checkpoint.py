#!/usr/bin/env python3
"""
Ingestion Checkpoint System

Provides checkpoint/resume functionality for the data ingestion pipeline.
Allows resuming from the last completed step after crashes or interruptions.

Usage:
    from ingestion_checkpoint import CheckpointManager
    
    checkpoint = CheckpointManager()
    
    # Save checkpoint after completing a step
    checkpoint.save(step="2.5", all_segments=segments, metadata=meta)
    
    # Load checkpoint at start
    data = checkpoint.load()
    if data:
        segments = data['all_segments']
        start_from = data['next_step']
"""
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
import pickle
import gzip

class CheckpointManager:
    """Manages checkpoint saving and loading for ingestion pipeline."""
    
    CHECKPOINT_FILE = ".ingestion_checkpoint.json.gz"
    CHECKPOINT_DATA_FILE = ".ingestion_checkpoint_data.pkl.gz"
    
    # Step order for resume logic (12-step refactored architecture)
    STEP_ORDER = [
        "1",      # Create CNN segments
        "2",      # Add intersections & permutations
        "3",      # Match parking meters (without schedules)
        "4",      # Add blockface geometries
        "5",      # Generate synthetic blockfaces
        "6",      # Attach meter schedules TO meters
        "7",      # Match parking regulations
        "8",      # Match street sweeping
        "9",      # Apply manual overrides
        "10",     # Aggregate blockface meter rules
        "11",     # Finalize cardinal direction
        "12"      # Save to database
    ]
    
    def __init__(self, checkpoint_dir: str = "."):
        """
        Initialize checkpoint manager.
        
        Args:
            checkpoint_dir: Directory to store checkpoint files
        """
        self.checkpoint_dir = checkpoint_dir
        self.checkpoint_path = os.path.join(checkpoint_dir, self.CHECKPOINT_FILE)
        self.data_path = os.path.join(checkpoint_dir, self.CHECKPOINT_DATA_FILE)
    
    def save(self, 
             step: str,
             all_segments: List[Dict],
             streets_metadata: Dict[str, Any],
             stats: Optional[Dict[str, Any]] = None) -> None:
        """
        Save checkpoint after completing a step.
        
        Args:
            step: Step number that was just completed (e.g., "2.5")
            all_segments: List of all street segments
            streets_metadata: Metadata dictionary
            stats: Optional statistics dictionary
        """
        # Determine next step
        try:
            current_idx = self.STEP_ORDER.index(step)
            next_step = self.STEP_ORDER[current_idx + 1] if current_idx + 1 < len(self.STEP_ORDER) else "complete"
        except ValueError:
            next_step = "unknown"
        
        # Save metadata (small, JSON)
        metadata = {
            "last_completed_step": step,
            "next_step": next_step,
            "timestamp": datetime.utcnow().isoformat(),
            "segment_count": len(all_segments),
            "stats": stats or {}
        }
        
        with gzip.open(self.checkpoint_path, 'wt', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        # Save data (large, pickle)
        data = {
            "all_segments": all_segments,
            "streets_metadata": streets_metadata
        }
        
        with gzip.open(self.data_path, 'wb') as f:
            pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
        
        print(f"✓ Checkpoint saved: Step {step} complete, resume from Step {next_step}")
    
    def load(self) -> Optional[Dict[str, Any]]:
        """
        Load checkpoint if it exists.
        
        Returns:
            Dictionary with checkpoint data, or None if no checkpoint exists
        """
        if not os.path.exists(self.checkpoint_path) or not os.path.exists(self.data_path):
            return None
        
        try:
            # Load metadata
            with gzip.open(self.checkpoint_path, 'rt', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # Load data
            with gzip.open(self.data_path, 'rb') as f:
                data = pickle.load(f)
            
            # Combine
            result = {**metadata, **data}
            
            print(f"✓ Checkpoint found: Last completed Step {metadata['last_completed_step']}")
            print(f"  Timestamp: {metadata['timestamp']}")
            print(f"  Segments: {metadata['segment_count']}")
            print(f"  Next step: {metadata['next_step']}")
            
            return result
            
        except Exception as e:
            print(f"⚠️  Failed to load checkpoint: {e}")
            print("  Starting fresh ingestion...")
            return None
    
    def clear(self) -> None:
        """Delete checkpoint files."""
        if os.path.exists(self.checkpoint_path):
            os.remove(self.checkpoint_path)
        if os.path.exists(self.data_path):
            os.remove(self.data_path)
        print("✓ Checkpoint cleared")
    
    def exists(self) -> bool:
        """Check if checkpoint exists."""
        return os.path.exists(self.checkpoint_path) and os.path.exists(self.data_path)
    
    def get_info(self) -> Optional[Dict[str, Any]]:
        """Get checkpoint info without loading full data."""
        if not os.path.exists(self.checkpoint_path):
            return None
        
        try:
            with gzip.open(self.checkpoint_path, 'rt', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None
    
    def should_resume_from(self, step: str) -> bool:
        """
        Check if we should resume from a specific step.
        
        Args:
            step: Step to check (e.g., "3")
            
        Returns:
            True if checkpoint exists and next_step <= step
        """
        info = self.get_info()
        if not info:
            return False
        
        try:
            next_idx = self.STEP_ORDER.index(info['next_step'])
            step_idx = self.STEP_ORDER.index(step)
            return next_idx <= step_idx
        except ValueError:
            return False


def add_checkpoint_args(parser):
    """
    Add checkpoint-related arguments to argparse parser.
    
    Usage:
        parser = argparse.ArgumentParser()
        add_checkpoint_args(parser)
        args = parser.parse_args()
    """
    parser.add_argument(
        '--resume',
        action='store_true',
        help='Resume from last checkpoint if available'
    )
    parser.add_argument(
        '--resume-from',
        type=str,
        choices=CheckpointManager.STEP_ORDER,
        help='Resume from specific step (ignores checkpoint)'
    )
    parser.add_argument(
        '--force-restart',
        action='store_true',
        help='Force full restart, ignore checkpoint'
    )
    parser.add_argument(
        '--clear-checkpoint',
        action='store_true',
        help='Clear checkpoint and exit'
    )
    parser.add_argument(
        '--checkpoint-info',
        action='store_true',
        help='Show checkpoint info and exit'
    )


if __name__ == "__main__":
    # Test checkpoint system
    import argparse
    
    parser = argparse.ArgumentParser(description="Test checkpoint system")
    add_checkpoint_args(parser)
    args = parser.parse_args()
    
    checkpoint = CheckpointManager()
    
    if args.clear_checkpoint:
        checkpoint.clear()
    elif args.checkpoint_info:
        info = checkpoint.get_info()
        if info:
            print(json.dumps(info, indent=2))
        else:
            print("No checkpoint found")
    else:
        # Test save/load
        print("Testing checkpoint system...")
        
        # Save test checkpoint
        test_segments = [{"cnn": "123000", "side": "L"}]
        test_metadata = {"test": "data"}
        checkpoint.save("2.5", test_segments, test_metadata, {"test_stat": 42})
        
        # Load checkpoint
        data = checkpoint.load()
        if data:
            print(f"Loaded {len(data['all_segments'])} segments")
            print(f"Next step: {data['next_step']}")
        
        # Clear
        checkpoint.clear()