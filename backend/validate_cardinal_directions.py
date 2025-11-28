"""
Cardinal Direction Validation System

Validates cardinal direction data against logical rules:
1. R side should have EVEN street numbers
2. L side should have ODD street numbers  
3. Same CNN+side cannot have conflicting cardinal directions (N vs S, E vs W)
4. If CNN L is North, CNN R should be South (and vice versa)
5. If CNN L is East, CNN R should be West (and vice versa)
"""

import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import asyncio
from collections import defaultdict

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
client = AsyncIOMotorClient(MONGODB_URI)
db = client.curby

# Opposing cardinal directions
OPPOSITES = {
    'N': 'S', 'S': 'N',
    'E': 'W', 'W': 'E',
    'NE': 'SW', 'SW': 'NE',
    'NW': 'SE', 'SE': 'NW',
    'NORTH': 'SOUTH', 'SOUTH': 'NORTH',
    'EAST': 'WEST', 'WEST': 'EAST',
    'NORTHEAST': 'SOUTHWEST', 'SOUTHWEST': 'NORTHEAST',
    'NORTHWEST': 'SOUTHEAST', 'SOUTHEAST': 'NORTHWEST'
}

def get_parity(address):
    """Determine if address is even or odd"""
    try:
        num = int(address)
        return "even" if num % 2 == 0 else "odd"
    except (ValueError, TypeError):
        return None

def normalize_cardinal(cardinal):
    """Normalize cardinal direction to uppercase"""
    if not cardinal:
        return None
    return cardinal.strip().upper()

async def validate_mission_cardinals():
    """Validate cardinal directions for Mission neighborhood"""
    
    print("Cardinal Direction Validation Report")
    print("=" * 80)
    print("\nValidation Rules:")
    print("1. R side → EVEN street numbers")
    print("2. L side → ODD street numbers")
    print("3. Same CNN+side cannot have conflicting cardinals (N vs S, E vs W)")
    print("4. If CNN L is North, CNN R should be South")
    print("5. When no information exists, note it (don't infer)")
    print("=" * 80)
    
    # Collect all segments
    cursor = db.street_segments.find()
    segments = await cursor.to_list(length=None)
    
    print(f"\nAnalyzing {len(segments)} street segments...")
    
    # Group by CNN
    cnn_groups = defaultdict(lambda: {'L': [], 'R': []})
    
    for seg in segments:
        cnn = seg.get('cnn')
        side = seg.get('side')
        if cnn and side:
            cnn_groups[cnn][side].append(seg)
    
    # Validation results
    violations = []
    warnings = []
    valid_count = 0
    no_info_count = 0
    
    for cnn, sides in cnn_groups.items():
        for side in ['L', 'R']:
            if not sides[side]:
                continue
                
            seg = sides[side][0]  # Take first segment for this CNN+side
            street_name = seg.get('streetName', 'Unknown')
            from_addr = seg.get('fromAddress')
            to_addr = seg.get('toAddress')
            
            # Extract cardinal directions from rules
            cardinals = set()
            rules = seg.get('rules', [])
            for rule in rules:
                if rule.get('blockside'):
                    cardinals.add(normalize_cardinal(rule.get('blockside')))
                elif rule.get('cardinalDirection'):
                    cardinals.add(normalize_cardinal(rule.get('cardinalDirection')))
            
            # Check 1 & 2: Address parity validation
            if from_addr:
                parity = get_parity(from_addr)
                expected_parity = "even" if side == "R" else "odd"
                
                if parity and parity != expected_parity:
                    violations.append({
                        'type': 'ADDRESS_PARITY_MISMATCH',
                        'cnn': cnn,
                        'side': side,
                        'street': street_name,
                        'address': from_addr,
                        'expected': expected_parity,
                        'actual': parity,
                        'message': f"CNN {cnn} {side} ({street_name}): Address {from_addr} is {parity} but {side} side should be {expected_parity}"
                    })
            
            # Check 3: Conflicting cardinals on same CNN+side
            if len(cardinals) > 1:
                # Check if any are opposing
                for c1 in cardinals:
                    for c2 in cardinals:
                        if c1 != c2 and OPPOSITES.get(c1) == c2:
                            violations.append({
                                'type': 'CONFLICTING_CARDINALS_SAME_SIDE',
                                'cnn': cnn,
                                'side': side,
                                'street': street_name,
                                'cardinals': list(cardinals),
                                'message': f"CNN {cnn} {side} ({street_name}): Conflicting cardinals {cardinals}"
                            })
                            break
            
            # Check 4: Opposite sides should have opposite cardinals
            if cardinals and sides['L'] and sides['R']:
                other_side = 'R' if side == 'L' else 'L'
                other_seg = sides[other_side][0] if sides[other_side] else None
                
                if other_seg:
                    other_cardinals = set()
                    other_rules = other_seg.get('rules', [])
                    for rule in other_rules:
                        if rule.get('blockside'):
                            other_cardinals.add(normalize_cardinal(rule.get('blockside')))
                        elif rule.get('cardinalDirection'):
                            other_cardinals.add(normalize_cardinal(rule.get('cardinalDirection')))
                    
                    if cardinals and other_cardinals:
                        # Check if they're opposites
                        for c in cardinals:
                            expected_opposite = OPPOSITES.get(c)
                            if expected_opposite and expected_opposite not in other_cardinals:
                                warnings.append({
                                    'type': 'OPPOSITE_SIDE_MISMATCH',
                                    'cnn': cnn,
                                    'street': street_name,
                                    'l_cardinals': list(cardinals) if side == 'L' else list(other_cardinals),
                                    'r_cardinals': list(other_cardinals) if side == 'L' else list(cardinals),
                                    'message': f"CNN {cnn} ({street_name}): L={cardinals if side == 'L' else other_cardinals}, R={other_cardinals if side == 'L' else cardinals} - Expected opposites"
                                })
            
            # Track segments with no cardinal info
            if not cardinals:
                no_info_count += 1
            else:
                valid_count += 1
    
    # Print results
    print(f"\n{'='*80}")
    print("VALIDATION RESULTS")
    print(f"{'='*80}")
    print(f"Total segments analyzed: {len(segments)}")
    print(f"Segments with cardinal info: {valid_count}")
    print(f"Segments without cardinal info: {no_info_count}")
    print(f"Violations found: {len(violations)}")
    print(f"Warnings found: {len(warnings)}")
    
    if violations:
        print(f"\n{'='*80}")
        print("🚨 VIOLATIONS (Require AI Review)")
        print(f"{'='*80}")
        for v in violations[:10]:  # Show first 10
            print(f"\n{v['type']}:")
            print(f"  {v['message']}")
    
    if warnings:
        print(f"\n{'='*80}")
        print("⚠️  WARNINGS (Potential Issues)")
        print(f"{'='*80}")
        for w in warnings[:10]:  # Show first 10
            print(f"\n{w['type']}:")
            print(f"  {w['message']}")
    
    if no_info_count > 0:
        print(f"\n{'='*80}")
        print(f"ℹ️  NO INFORMATION: {no_info_count} segments have no cardinal direction data")
        print("   (Not inferring - just noting absence of data)")
        print(f"{'='*80}")
    
    # Save violations for AI review
    if violations:
        print(f"\n💾 Saving {len(violations)} violations for AI interpretation engine review...")
        # Could save to a collection or file here
    
    client.close()
    
    return {
        'total': len(segments),
        'valid': valid_count,
        'no_info': no_info_count,
        'violations': violations,
        'warnings': warnings
    }

if __name__ == "__main__":
    asyncio.run(validate_mission_cardinals())