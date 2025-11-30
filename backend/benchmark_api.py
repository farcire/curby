import requests
import time
import statistics

BASE_URL = "http://localhost:8000/api/v1/blockfaces"

# Test cases: (lat, lng, radius_meters, description)
TEST_CASES = [
    (37.76272, -122.40920, 300, "Small Radius (300m)"),
    (37.76272, -122.40920, 1000, "Medium Radius (1000m)"),
    (37.75904, -122.41498, 2600, "Large Radius (2600m - ~7500 items)")
]

def run_benchmark():
    print(f"Benchmarking API at {BASE_URL}...\n")
    print(f"{'Test Case':<30} | {'Items':<10} | {'Time (s)':<10} | {'Status':<10}")
    print("-" * 70)

    for lat, lng, radius, desc in TEST_CASES:
        times = []
        item_count = 0
        status = "Fail"
        
        # Run 3 times to get an average
        for _ in range(3):
            start_time = time.time()
            try:
                response = requests.get(
                    BASE_URL, 
                    params={"lat": lat, "lng": lng, "radius_meters": radius}
                )
                end_time = time.time()
                
                if response.status_code == 200:
                    data = response.json()
                    item_count = len(data)
                    times.append(end_time - start_time)
                    status = "OK"
                else:
                    print(f"Error: {response.status_code}")
            except Exception as e:
                print(f"Exception: {e}")

        if times:
            avg_time = statistics.mean(times)
            print(f"{desc:<30} | {item_count:<10} | {avg_time:<10.4f} | {status:<10}")

if __name__ == "__main__":
    run_benchmark()