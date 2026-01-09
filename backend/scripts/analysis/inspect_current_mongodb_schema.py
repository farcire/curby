"""
Inspect Current MongoDB Schema
==============================
Generates a complete list of all fields in the street_segments collection.
"""

import os
import asyncio
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import json

load_dotenv()

async def inspect_schema():
    """Inspect and document all fields in street_segments collection"""
    
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        raise ValueError("MONGODB_URI not found in .env file")
    
    client = AsyncIOMotorClient(mongodb_uri)
    db = client.curby
    
    print("Connecting to MongoDB...")
    await db.command('ping')
    print("✓ Connected\n")
    
    # Get a sample document
    print("Fetching sample document...")
    sample = await db.street_segments.find_one()
    
    if not sample:
        print("ERROR: No documents found in street_segments collection")
        client.close()
        return
    
    print(f"✓ Found sample document (CNN: {sample.get('cnn')}, Side: {sample.get('side')})\n")
    
    # Recursively extract all field paths
    def extract_fields(obj, prefix=""):
        """Recursively extract all field paths from a document"""
        fields = []
        
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key == '_id':
                    continue  # Skip MongoDB internal ID
                
                field_path = f"{prefix}.{key}" if prefix else key
                
                # Determine type
                if isinstance(value, dict):
                    fields.append({
                        'path': field_path,
                        'type': 'object',
                        'sample': None
                    })
                    # Recurse into nested object
                    fields.extend(extract_fields(value, field_path))
                elif isinstance(value, list):
                    if len(value) > 0:
                        first_item = value[0]
                        if isinstance(first_item, dict):
                            fields.append({
                                'path': field_path,
                                'type': 'array[object]',
                                'sample': f"{len(value)} items"
                            })
                            # Recurse into first array item
                            fields.extend(extract_fields(first_item, f"{field_path}[0]"))
                        else:
                            fields.append({
                                'path': field_path,
                                'type': f'array[{type(first_item).__name__}]',
                                'sample': str(value[0]) if len(str(value[0])) < 50 else str(value[0])[:50] + "..."
                            })
                    else:
                        fields.append({
                            'path': field_path,
                            'type': 'array[empty]',
                            'sample': '[]'
                        })
                else:
                    value_type = type(value).__name__
                    sample_value = str(value) if len(str(value)) < 50 else str(value)[:50] + "..."
                    fields.append({
                        'path': field_path,
                        'type': value_type,
                        'sample': sample_value
                    })
        
        return fields
    
    # Extract all fields
    all_fields = extract_fields(sample)
    
    # Group by top-level category
    categories = {}
    for field in all_fields:
        top_level = field['path'].split('.')[0].split('[')[0]
        if top_level not in categories:
            categories[top_level] = []
        categories[top_level].append(field)
    
    # Generate report
    report = []
    report.append("=" * 80)
    report.append("MONGODB STREET_SEGMENTS SCHEMA")
    report.append("=" * 80)
    report.append(f"\nSample Document: CNN {sample.get('cnn')} Side {sample.get('side')}")
    report.append(f"Total Fields: {len(all_fields)}")
    report.append(f"Top-Level Categories: {len(categories)}")
    report.append("\n" + "=" * 80)
    
    # Sort categories for consistent output
    for category in sorted(categories.keys()):
        fields = categories[category]
        report.append(f"\n## {category.upper()}")
        report.append("-" * 80)
        
        for field in fields:
            path = field['path']
            field_type = field['type']
            sample = field['sample']
            
            if sample:
                report.append(f"  {path:<50} {field_type:<20} = {sample}")
            else:
                report.append(f"  {path:<50} {field_type:<20}")
    
    report.append("\n" + "=" * 80)
    report.append("END OF SCHEMA")
    report.append("=" * 80)
    
    # Print to console
    report_text = "\n".join(report)
    print(report_text)
    
    # Save to file
    output_file = "mongodb_schema_current.txt"
    with open(output_file, 'w') as f:
        f.write(report_text)
    
    print(f"\n✓ Schema report saved to: {output_file}")
    
    # Also save sample document as JSON for reference
    sample_file = "mongodb_sample_document.json"
    # Remove _id for cleaner output
    if '_id' in sample:
        del sample['_id']
    
    with open(sample_file, 'w') as f:
        json.dump(sample, f, indent=2, default=str)
    
    print(f"✓ Sample document saved to: {sample_file}")
    
    # Check for modalContent field specifically
    print("\n" + "=" * 80)
    print("MODAL CONTENT CHECK")
    print("=" * 80)
    
    has_modal_content = 'modalContent' in sample
    print(f"Has modalContent field: {has_modal_content}")
    
    if has_modal_content:
        modal = sample.get('modalContent', {})
        print(f"  - location_text: {bool(modal.get('location_text'))}")
        print(f"  - cross_streets_text: {bool(modal.get('cross_streets_text'))}")
        print(f"  - rules: {len(modal.get('rules', []))} items")
        print(f"  - next_restriction: {bool(modal.get('next_restriction'))}")
    else:
        print("  ⚠️  modalContent field is MISSING - data needs re-ingestion")
    
    client.close()
    print("\n✓ Inspection complete")

if __name__ == "__main__":
    asyncio.run(inspect_schema())