from shapely.geometry import shape, mapping, LineString
import json

def test_offset():
    # Example centerline (roughly West to East)
    # 20th St coordinates from previous log: [[-122.408903725, 37.759246641]]... 
    # Let's use a simple horizontal line for testing
    coords = [[0.0, 0.0], [1.0, 0.0]] 
    line = LineString(coords)
    
    print(f"Original: {line}")
    
    # Offset distance in degrees (approx)
    # 0.0001 deg ~ 11 meters. We want maybe 3-4 meters offset? 
    # So ~0.00004 degrees.
    offset_dist = 0.00004
    
    # Shapely parallel_offset:
    # side: 'left' or 'right' relative to line direction
    
    # LEFT offset
    left_line = line.parallel_offset(offset_dist, 'left')
    print(f"\nLeft Offset (dist={offset_dist}):")
    print(left_line)
    
    # RIGHT offset
    right_line = line.parallel_offset(offset_dist, 'right')
    print(f"\nRight Offset (dist={offset_dist}):")
    print(right_line)
    
    # Check orientation (parallel_offset might reverse direction for right side)
    print(f"\nLeft coords: {list(left_line.coords)}")
    print(f"Right coords: {list(right_line.coords)}")

    # NOTE: parallel_offset('right') in shapely often returns the line in reverse order!
    # We should normalize it to match the original direction if needed, 
    # though for display it might not matter unless we use arrows.
    
    # Test with real coords
    real_coords = [[-122.409770121414, 37.759194010363], [-122.408903725589, 37.759246640958]]
    real_line = LineString(real_coords)
    print(f"\nReal Line: {real_line}")
    
    real_left = real_line.parallel_offset(offset_dist, 'left')
    real_right = real_line.parallel_offset(offset_dist, 'right')
    
    print(f"Real Left: {real_left}")
    print(f"Real Right: {real_right}")

if __name__ == "__main__":
    test_offset()