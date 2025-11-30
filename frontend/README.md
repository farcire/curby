# Curby - Frontend

Curby is a mobile-first Progressive Web App (PWA) designed to simplify street parking in San Francisco. It provides accurate, real-time parking eligibility for the Mission and SOMA neighborhoods.

## Key Features

- **Interactive Map:** Displays parking legality for all blockfaces within the Mission & SOMA.
- **Three-Tier Zoom:** Specialized zoom levels for Immediate Vicinity, Walking Distance, and Neighborhood Context.
- **Unrestricted Exploration:** Pan freely across the city without boundary limits.
- **Dynamic Data Fetching:** Automatically fetches parking regulations based on the visible map area.
- **Duration Slider:** Intuitive "pill" slider to check parking legality for specific durations (1h - 24h).
- **Resident Focused:** Designed for SF residents running errands or visiting friends.
- **PWA Support:** Installable on mobile devices with offline capabilities.
- **Geolocation:** Uses actual device location for map centering and user position marker.

## Tech Stack

- **Framework:** React (Vite)
- **Language:** TypeScript
- **Map:** Leaflet (React Leaflet) with OpenStreetMap tiles
- **Styling:** Tailwind CSS
- **Icons:** Lucide React
- **PWA:** vite-plugin-pwa

## Getting Started

1.  Install dependencies:
    ```bash
    npm install
    ```

2.  Run the development server:
    ```bash
    npm run dev
    ```

3.  Build for production:
    ```bash
    npm run build
    ```

## Recent Updates

### Navigation & Zoom Overhaul (2025-11-29)
- **Smart Geolocation:** Map centers on user location exactly once upon initialization.
- **Three-Tier Zoom:** Implemented distinct zoom levels for optimal viewing (Vicinity, Walking, Neighborhood).
- **Free Navigation:** Disabled auto-centering to allow unrestricted map panning.
- **Unrestricted Exploration:** Removed neighborhood boundaries to allow city-wide exploration.
- **Return Control:** Added "Return to Location" button to manually re-center the map.

### Location Marker Centering Fix (2025-11-28)
- Fixed issue where location marker appeared at bottom of map instead of centered
- Removed hardcoded demo location from ParkingNavigator component
- Implemented proper device geolocation in both Map and Navigator views
- Added dynamic map centering when user location becomes available
- Location marker now correctly appears at center of map view at app initialization
