# Curby - Frontend

**Last Updated:** December 1, 2024
**Status:** ✅ Beta Ready

Curby is a mobile-first Progressive Web App (PWA) designed to simplify street parking in San Francisco. It provides accurate, real-time parking eligibility for the Mission and SOMA neighborhoods.

## Key Features

- **Interactive Map:** Displays parking legality for all blockfaces within the Mission & SOMA.
- **Enhanced Location Context:** Shows street name, cardinal direction (e.g., "North side"), and address range (e.g., "100-199") for clear identification.
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

### Beta Release (December 2024)
- ✅ **Complete Feature Set:** All MVP features implemented and tested
- ✅ **PWA Ready:** Installable on mobile devices with offline support
- ✅ **Performance Optimized:** <100ms response time for standard queries
- ✅ **Data Complete:** 34,292 street segments with 100% Mission District coverage

### Navigation & Zoom Overhaul (November 2024)
- **Smart Geolocation:** Map centers on user location exactly once upon initialization
- **Three-Tier Zoom:** Distinct zoom levels for optimal viewing (Vicinity, Walking, Neighborhood)
- **Free Navigation:** Unrestricted map panning without auto-centering
- **City-Wide Exploration:** Removed neighborhood boundaries
- **Return Control:** "Return to Location" button for manual re-centering

### Location Marker Centering Fix (November 2024)
- Fixed location marker positioning (now centered correctly)
- Removed hardcoded demo locations
- Implemented proper device geolocation
- Dynamic map centering on location availability
