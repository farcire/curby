# Curby Enhancement - Implementation Plan for Tonight
**Date:** December 4, 2024  
**Goal:** Implement all four enhancements in one session

## Quick Summary

You already have everything you need:
- ✅ Street names in database
- ✅ Address ranges (`fromAddress`, `toAddress`)
- ✅ Intersection data
- ✅ CNN-based architecture
- ✅ Leaflet for maps

**No external APIs needed!** Use your own data for address search.

---

## Implementation Order (4-6 hours total)

### 1. Enhanced RPP Logic (1 hour) - HIGHEST IMPACT

**File:** `frontend/src/utils/rppEvaluator.ts` (NEW)

```typescript
export interface RPPEvaluation {
  canPark: boolean;
  reason: string;
  visitorLimitMinutes?: number;
}

export function evaluateRPPZone(
  regulation: string,
  zone: string,
  durationMinutes: number
): RPPEvaluation {
  const text = regulation.toLowerCase();
  
  // Extract visitor time limit
  // Patterns: "2 hour visitor", "visitors 2 hours", "2hr visitor parking"
  const patterns = [
    /visitor[s]?\s+(\d+)\s+hour[s]?/i,
    /(\d+)\s*(?:hr|hour)[s]?\s+visitor/i,
    /(\d+)\s*(?:hr|hour)[s]?\s+(?:for\s+)?non-permit/i
  ];
  
  let visitorLimitMinutes = 120; // Default 2hr for SF
  
  for (const pattern of patterns) {
    const match = text.match(pattern);
    if (match) {
      visitorLimitMinutes = parseInt(match[1]) * 60;
      break;
    }
  }
  
  // Can user park for their full duration?
  if (durationMinutes <= visitorLimitMinutes) {
    return {
      canPark: true,
      reason: `${visitorLimitMinutes / 60}hr visitor parking (Zone ${zone})`,
      visitorLimitMinutes
    };
  }
  
  return {
    canPark: false,
    reason: `Your ${durationMinutes / 60}hr stay exceeds ${visitorLimitMinutes / 60}hr visitor limit`,
    visitorLimitMinutes
  };
}
```

**File:** `frontend/src/utils/ruleEngine.ts` (MODIFY)

```typescript
import { evaluateRPPZone } from './rppEvaluator';

// In generateLegalityResult function, replace RPP case:
case 'rpp-zone':
  const zone = primaryRule.metadata?.permitZone || 'Unknown';
  const rppEval = evaluateRPPZone(
    primaryRule.description,
    zone,
    durationMinutes
  );
  
  if (!rppEval.canPark) {
    status = 'illegal';
    explanation = `Don't park here! ${rppEval.reason}`;
  } else {
    status = 'legal';
    explanation = `You can park here! ${rppEval.reason}`;
  }
  break;
```

---

### 2. Simplified Tap Experience (1 hour)

**File:** `frontend/src/components/BlockfaceDetail.tsx` (REFACTOR)

```typescript
export function BlockfaceDetail({ 
  blockface, 
  legalityResult, 
  onReportError, 
  onClose 
}: BlockfaceDetailProps) {
  
  // Build combined explanation
  const buildExplanation = () => {
    const parts: string[] = [];
    
    // Add all applicable rules
    legalityResult.applicableRules.forEach(rule => {
      if (rule.type === 'meter') {
        const rate = rule.metadata?.meterRate || 3.50;
        parts.push(`Pay meter $${rate}/hr`);
      } else if (rule.type === 'time-limit') {
        const limit = rule.metadata?.timeLimit || 120;
        parts.push(`${limit / 60}hr time limit`);
      } else if (rule.type === 'rpp-zone') {
        // Already handled in explanation
      } else {
        parts.push(rule.description);
      }
    });
    
    return parts.join(', ');
  };
  
  const combinedExplanation = buildExplanation();
  
  // Calculate cost if meters apply
  const meterRule = legalityResult.applicableRules.find(r => r.type === 'meter');
  const costEstimate = meterRule ? 
    (durationMinutes / 60) * (meterRule.metadata?.meterRate || 3.50) : 
    null;
  
  return (
    <div className="fixed inset-x-0 bottom-0 z-50 flex justify-center p-3">
      <div className="w-full max-w-sm bg-white rounded-xl shadow-2xl overflow-hidden">
        
        {/* Status Header */}
        <div className={`px-4 py-3 ${
          legalityResult.status === 'legal' 
            ? 'bg-gradient-to-r from-green-500 to-emerald-600' 
            : 'bg-gradient-to-r from-red-500 to-rose-600'
        } text-white flex items-center justify-between`}>
          <div className="flex items-center gap-2">
            <span className="text-xl">
              {legalityResult.status === 'legal' ? '✅' : '🚫'}
            </span>
            <span className="font-bold">
              {legalityResult.status === 'legal' 
                ? 'You can park here!' 
                : "Don't park here!"}
            </span>
          </div>
          <button onClick={onClose} className="text-white/80 hover:text-white">
            <X className="h-5 w-5" />
          </button>
        </div>
        
        {/* Content */}
        <div className="px-4 py-3 space-y-3">
          
          {/* Location */}
          <div className="flex items-center gap-2 text-sm text-gray-700">
            <MapPin className="h-4 w-4 text-purple-600" />
            <span className="font-semibold">{blockface.streetName}</span>
            <span className="text-gray-500">
              ({blockface.cardinalDirection || blockface.side}
              {blockface.fromAddress && blockface.toAddress 
                ? `, ${blockface.fromAddress}-${blockface.toAddress}` 
                : ''})
            </span>
          </div>
          
          {/* Summary */}
          <div className="bg-gray-50 rounded-lg p-3">
            <h3 className="text-xs font-bold text-gray-700 mb-1">SUMMARY:</h3>
            <p className="text-sm text-gray-900">{legalityResult.explanation}</p>
            {combinedExplanation && (
              <p className="text-sm text-gray-700 mt-1">{combinedExplanation}</p>
            )}
            {costEstimate && (
              <p className="text-sm text-purple-600 font-semibold mt-1">
                Est. cost: ${costEstimate.toFixed(2)}
              </p>
            )}
          </div>
          
          {/* All Rules */}
          <div>
            <h3 className="text-xs font-bold text-gray-700 mb-1">ALL RULES:</h3>
            <ul className="space-y-1">
              {legalityResult.applicableRules.map((rule, idx) => (
                <li key={idx} className="text-xs text-gray-600 pl-3 relative">
                  <span className="absolute left-0 text-purple-600">•</span>
                  {rule.description}
                </li>
              ))}
            </ul>
          </div>
          
          {/* Next Restriction */}
          {legalityResult.status === 'legal' && getNextRestriction() && (
            <div className="bg-amber-50 rounded-lg p-2 border border-amber-200 flex items-start gap-2">
              <AlertCircle className="h-4 w-4 text-amber-600 flex-shrink-0 mt-0.5" />
              <div className="text-xs text-amber-900">
                <span className="font-semibold">Next restriction:</span>{' '}
                {formatNextRestriction(getNextRestriction())}
              </div>
            </div>
          )}
          
          {/* Actions */}
          <div className="flex items-center justify-between pt-2 border-t border-gray-100">
            <button
              onClick={onReportError}
              className="text-xs text-purple-600 hover:text-purple-700 font-medium"
            >
              Report Error
            </button>
            <button
              onClick={() => {
                const lat = blockface.geometry.coordinates[0][1];
                const lng = blockface.geometry.coordinates[0][0];
                const url = `https://maps.google.com/?q=${lat},${lng}`;
                window.open(url, '_blank');
              }}
              className="text-xs text-blue-600 hover:text-blue-700 font-medium"
            >
              Get Directions →
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
```

---

### 3. Out-of-SF Modal (30 minutes)

**File:** `frontend/src/utils/geoFence.ts` (NEW)

```typescript
export const SF_BOUNDS = {
  north: 37.8324,
  south: 37.7034,
  east: -122.3482,
  west: -122.5155
};

export const SF_CENTER: [number, number] = [37.7749, -122.4194];

export function isInSanFrancisco(lat: number, lng: number): boolean {
  return lat >= SF_BOUNDS.south && 
         lat <= SF_BOUNDS.north &&
         lng >= SF_BOUNDS.west && 
         lng <= SF_BOUNDS.east;
}

export function getDistanceToSF(lat: number, lng: number): number {
  // Haversine distance to SF center
  const R = 6371; // Earth radius in km
  const dLat = (SF_CENTER[0] - lat) * Math.PI / 180;
  const dLng = (SF_CENTER[1] - lng) * Math.PI / 180;
  const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
            Math.cos(lat * Math.PI / 180) * Math.cos(SF_CENTER[0] * Math.PI / 180) *
            Math.sin(dLng/2) * Math.sin(dLng/2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  return R * c;
}
```

**File:** `frontend/src/components/OutOfBoundsModal.tsx` (NEW)

```typescript
interface OutOfBoundsModalProps {
  distanceKm: number;
  onViewSF: () => void;
  onSearchAddress: () => void;
  onDismiss: () => void;
}

export function OutOfBoundsModal({ 
  distanceKm, 
  onViewSF, 
  onSearchAddress,
  onDismiss 
}: OutOfBoundsModalProps) {
  const distanceMiles = (distanceKm * 0.621371).toFixed(1);
  const isNearSF = distanceKm < 5;
  
  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-md w-full p-6">
        
        <div className="text-center mb-4">
          <div className="text-4xl mb-2">{isNearSF ? '📍' : '🌉'}</div>
          <h2 className="text-xl font-bold text-gray-900">
            {isNearSF 
              ? "You're near San Francisco" 
              : `You're ${distanceMiles} miles from SF`}
          </h2>
          <p className="text-gray-600 mt-2">
            Curby shows parking info for San Francisco only.
          </p>
        </div>
        
        <div className="space-y-2">
          <button
            onClick={onViewSF}
            className="w-full bg-purple-600 hover:bg-purple-700 text-white font-semibold py-3 px-4 rounded-lg transition-colors"
          >
            View SF Map
          </button>
          <button
            onClick={onSearchAddress}
            className="w-full bg-gray-100 hover:bg-gray-200 text-gray-900 font-semibold py-3 px-4 rounded-lg transition-colors"
          >
            Search SF Address
          </button>
          <button
            onClick={onDismiss}
            className="w-full text-gray-600 hover:text-gray-900 font-medium py-2 transition-colors"
          >
            Dismiss
          </button>
        </div>
        
        {isNearSF && (
          <p className="text-xs text-gray-500 text-center mt-4">
            Tip: Curby works within SF city limits only
          </p>
        )}
      </div>
    </div>
  );
}
```

**File:** `frontend/src/pages/Index.tsx` (MODIFY)

```typescript
import { isInSanFrancisco, getDistanceToSF, SF_CENTER } from '@/utils/geoFence';
import { OutOfBoundsModal } from '@/components/OutOfBoundsModal';

// Add state
const [showOutOfBoundsModal, setShowOutOfBoundsModal] = useState(false);
const [distanceToSF, setDistanceToSF] = useState<number>(0);

// Modify geolocation effect
useEffect(() => {
  if ('geolocation' in navigator) {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const userLoc: [number, number] = [
          position.coords.latitude,
          position.coords.longitude
        ];
        setUserLocation(userLoc);
        
        // Check if in SF
        if (!isInSanFrancisco(userLoc[0], userLoc[1])) {
          const distance = getDistanceToSF(userLoc[0], userLoc[1]);
          setDistanceToSF(distance);
          setShowOutOfBoundsModal(true);
          // Load SF map in background
          loadSFMTAData(SF_CENTER[0], SF_CENTER[1], 500);
        } else {
          loadSFMTAData(userLoc[0], userLoc[1], 300);
        }
        setHasInitialized(true);
      }
    );
  }
}, []);

// Add modal to render
{showOutOfBoundsModal && (
  <OutOfBoundsModal
    distanceKm={distanceToSF}
    onViewSF={() => setShowOutOfBoundsModal(false)}
    onSearchAddress={() => {
      setShowOutOfBoundsModal(false);
      setShowAddressSearch(true);
    }}
    onDismiss={() => setShowOutOfBoundsModal(false)}
  />
)}
```

---

### 4. Address Search with Your Own Data (2 hours)

**Backend API:** `backend/main.py` (ADD ENDPOINT)

```python
@app.get("/api/v1/search")
async def search_address(q: str, limit: int = 10):
    """
    Search for addresses and intersections using existing data.
    No external API needed - uses street_segments collection.
    """
    if not q or len(q) < 2:
        return []
    
    query_lower = q.lower().strip()
    results = []
    
    # Search by street name
    street_matches = await db.street_segments.find({
        "streetName": {"$regex": f"^{query_lower}", "$options": "i"}
    }).limit(limit).to_list(None)
    
    for match in street_matches:
        # Get center point of geometry
        coords = match["centerlineGeometry"]["coordinates"]
        center_lat = sum(c[1] for c in coords) / len(coords)
        center_lng = sum(c[0] for c in coords) / len(coords)
        
        # Build display name
        display_name = f"{match['streetName']}"
        if match.get('fromAddress') and match.get('toAddress'):
            display_name += f" ({match['fromAddress']}-{match['toAddress']})"
        if match.get('fromStreet') and match.get('toStreet'):
            display_name += f" between {match['fromStreet']} & {match['toStreet']}"
        
        results.append({
            "id": match["id"],
            "name": match["streetName"],
            "displayName": display_name,
            "coordinates": [center_lng, center_lat],
            "type": "street"
        })
    
    # Search by address number + street name
    if query_lower[0].isdigit():
        parts = query_lower.split(maxsplit=1)
        if len(parts) == 2:
            number, street = parts
            try:
                addr_num = int(number)
                # Find segments where address is in range
                address_matches = await db.street_segments.find({
                    "streetName": {"$regex": f"^{street}", "$options": "i"},
                    "fromAddress": {"$lte": str(addr_num)},
                    "toAddress": {"$gte": str(addr_num)}
                }).limit(5).to_list(None)
                
                for match in address_matches:
                    coords = match["centerlineGeometry"]["coordinates"]
                    center_lat = sum(c[1] for c in coords) / len(coords)
                    center_lng = sum(c[0] for c in coords) / len(coords)
                    
                    results.append({
                        "id": match["id"],
                        "name": f"{number} {match['streetName']}",
                        "displayName": f"{number} {match['streetName']} ({match.get('cardinalDirection', match['side'])} side)",
                        "coordinates": [center_lng, center_lat],
                        "type": "address"
                    })
            except ValueError:
                pass
    
    return results[:limit]
```

**Frontend:** `frontend/src/components/AddressSearch.tsx` (NEW)

```typescript
import { useState, useEffect } from 'react';
import { Search, X } from 'lucide-react';

interface SearchResult {
  id: string;
  name: string;
  displayName: string;
  coordinates: [number, number];
  type: 'street' | 'address';
}

interface AddressSearchProps {
  onLocationSelect: (coords: [number, number], name: string) => void;
  onClose: () => void;
}

export function AddressSearch({ onLocationSelect, onClose }: AddressSearchProps) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  
  useEffect(() => {
    const searchAddress = async () => {
      if (query.length < 2) {
        setResults([]);
        return;
      }
      
      setIsSearching(true);
      try {
        const response = await fetch(
          `${import.meta.env.VITE_API_URL}/api/v1/search?q=${encodeURIComponent(query)}&limit=10`
        );
        const data = await response.json();
        setResults(data);
      } catch (error) {
        console.error('Search error:', error);
        setResults([]);
      } finally {
        setIsSearching(false);
      }
    };
    
    const timer = setTimeout(searchAddress, 300); // Debounce
    return () => clearTimeout(timer);
  }, [query]);
  
  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-md w-full max-h-[80vh] flex flex-col">
        
        {/* Header */}
        <div className="p-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-lg font-bold text-gray-900">Search SF Address</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="h-5 w-5" />
          </button>
        </div>
        
        {/* Search Input */}
        <div className="p-4 border-b border-gray-200">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Enter address or street name..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              autoFocus
            />
          </div>
        </div>
        
        {/* Results */}
        <div className="flex-1 overflow-y-auto p-2">
          {isSearching && (
            <div className="text-center py-8 text-gray-500">Searching...</div>
          )}
          
          {!isSearching && query.length >= 2 && results.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              No results found. Try a different address.
            </div>
          )}
          
          {results.map((result) => (
            <button
              key={result.id}
              onClick={() => {
                onLocationSelect(
                  [result.coordinates[1], result.coordinates[0]], // lat, lng
                  result.displayName
                );
                onClose();
              }}
              className="w-full text-left p-3 hover:bg-gray-50 rounded-lg transition-colors"
            >
              <div className="font-medium text-gray-900">{result.name}</div>
              <div className="text-sm text-gray-500">{result.displayName}</div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
```

**Frontend:** `frontend/src/pages/Index.tsx` (ADD STATE & HANDLERS)

```typescript
const [showAddressSearch, setShowAddressSearch] = useState(false);
const [searchedLocation, setSearchedLocation] = useState<[number, number] | null>(null);
const [searchedLocationName, setSearchedLocationName] = useState<string>('');

const handleLocationSelect = (coords: [number, number], name: string) => {
  setSearchedLocation(coords);
  setSearchedLocationName(name);
  loadSFMTAData(coords[0], coords[1], 300);
};

// Add to render
{showAddressSearch && (
  <AddressSearch
    onLocationSelect={handleLocationSelect}
    onClose={() => setShowAddressSearch(false)}
  />
)}
```

**Frontend:** `frontend/src/components/MapView.tsx` (ADD SEARCHED LOCATION MARKER)

```typescript
// Add to MapView props
interface MapViewProps {
  // ... existing props
  searchedLocation?: [number, number];
  searchedLocationName?: string;
}

// Add effect for searched location marker
useEffect(() => {
  if (searchedLocation && mapRef.current) {
    // Remove previous marker if exists
    if (searchedMarkerRef.current) {
      searchedMarkerRef.current.remove();
    }
    
    // Add red pin marker
    searchedMarkerRef.current = L.marker(searchedLocation, {
      icon: L.divIcon({
        className: 'searched-location-marker',
        html: '<div style="font-size: 30px;">📍</div>',
        iconSize: [30, 30],
        iconAnchor: [15, 30]
      })
    }).addTo(mapRef.current);
    
    // Add popup
    if (searchedLocationName) {
      searchedMarkerRef.current.bindPopup(searchedLocationName).openPopup();
    }
    
    // Center map
    mapRef.current.setView(searchedLocation, 17);
  }
}, [searchedLocation, searchedLocationName]);
```

---

## Testing Checklist

### RPP Logic
- [ ] Test with Mission District RPP Zone W (20th & Valencia)
- [ ] Verify 2hr visitor parking shows as legal
- [ ] Verify 3hr duration shows as illegal (exceeds limit)

### Tap Experience
- [ ] Tap blockface, verify single view (no expansion)
- [ ] Verify summary shows combined rules
- [ ] Verify full rules list displays
- [ ] Verify cost estimate for meters
- [ ] Test "Get Directions" button

### Out-of-SF Modal
- [ ] Test in Oakland (near SF message)
- [ ] Test in San Jose (X miles message)
- [ ] Verify "View SF Map" loads SF
- [ ] Verify "Search SF Address" opens search

### Address Search
- [ ] Search "Mission St" - verify results
- [ ] Search "1234 Mission St" - verify address match
- [ ] Search "20th" - verify street results
- [ ] Verify map centers on selected result
- [ ] Verify red pin appears
- [ ] Verify popup shows address name

---

## Deployment Steps

1. **Commit changes:**
```bash
git add .
git commit -m "feat: Enhanced RPP logic, simplified tap experience, out-of-SF modal, address search"
git push origin main
```

2. **Test locally:**
- Backend: `cd backend && uvicorn main:app --reload`
- Frontend: `cd frontend && npm run dev`

3. **Deploy:**
- Frontend: Push to Vercel/Netlify
- Backend: Push to Railway/Render

---

## Estimated Time

- RPP Logic: 1 hour
- Tap Experience: 1 hour
- Out-of-SF Modal: 30 minutes
- Address Search: 2 hours
- Testing: 30 minutes
- **Total: 5 hours**

---

## Key Benefits

1. **No external APIs** - Use your own data for search
2. **50% faster** - With message caching (can add later)
3. **Better UX** - Binary status, clear messaging, address search
4. **Smart RPP** - Fixes major UX issue with visitor parking

Ready to implement tonight! 🚀