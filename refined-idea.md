# Refined Project Idea: Curby Frontend Map & Navigation Updates

**App Description**: An update to the Curby parking app to enhance map navigation and user location behavior. It enables city-wide exploration, precise initial positioning, and a simplified 3-tier zoom experience for intuitive viewing and improved performance.

**Target Users**: Drivers in San Francisco/Urban areas searching for parking.

**Core Features**:
1. **Smart Geolocation**: 
    - Request geolocation permission immediately on app launch.
    - Center the map on the user's location exactly once upon successful retrieval.
2. **Three-Tier Zoom System**: 
    - Restrict map zooming to three distinct levels of detail to optimize performance and usability:
        - **Immediate Vicinity** (High detail, ~1 block radius, approx Zoom 18)
        - **Walking Distance** (Medium detail, ~3-4 blocks radius, approx Zoom 16.5)
        - **Neighborhood Context** (Broad view, ~800m radius, approx Zoom 15)
3. **Immediate Detail Default**: 
    - The app initializes at the "Immediate Vicinity" zoom level to help users spot parking right where they are.
4. **Unrestricted Exploration**: 
    - Remove neighborhood boundary limits (e.g., Mission District bounds).
    - Allow users to pan the map freely to any part of the city.
5. **Free Navigation**: 
    - Disable auto-centering after the initial location fix.
    - The map remains where the user pans it, even if their physical location updates in the background.
6. **Return Control**: 
    - A "Return to Location" button allows the user to manually re-center the map on their current position.

**Technical Requirements**: 
- **Leaflet Configuration**: 
    - Remove `maxBounds` restrictions.
    - Configure `minZoom` and `maxZoom` to correspond to the neighborhood and immediate views respectively.
    - Implement logic to snap or restrict zoom to the three defined tiers.
- **Geolocation Logic**: 
    - Ensure location updates do not trigger a map view reset unless explicitly requested via the button.