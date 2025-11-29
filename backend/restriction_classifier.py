"""
Restriction Classifier

Routes parking restrictions to the appropriate processing engine:
1. Deterministic Parser: For standard patterns (meters, street cleaning)
2. AI Engine: For complex or ambiguous regulations
"""

def classify_restriction(source_dataset: str, record: dict) -> str:
    """
    Determine which engine should process a restriction.
    
    Args:
        source_dataset: The ID or name of the source dataset.
        record: The raw data record.
        
    Returns:
        'parser' or 'ai'
    """
    # 1. Meters (Deterministic)
    # Dataset ID: 6cqg-dxku (Operating Schedules) or 8vzz-qzz9 (Meters)
    if source_dataset in ['6cqg-dxku', '8vzz-qzz9', 'meters']:
        return 'parser'
        
    # 2. Street Sweeping (Deterministic)
    # Dataset ID: yhqp-riqs
    if source_dataset in ['yhqp-riqs', 'street_cleaning']:
        return 'parser'
        
    # 3. General Regulations (AI by default, unless simple)
    # Dataset ID: hi6h-neyh
    if source_dataset in ['hi6h-neyh', 'regulations']:
        # TODO: Add regex checks here for simple patterns that don't need AI
        # e.g. "NO PARKING 2AM-6AM" could be parsed deterministically
        return 'ai'
        
    # Default to AI for unknown sources to be safe
    return 'ai'