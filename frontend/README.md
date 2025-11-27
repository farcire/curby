# Curby - Frontend

Curby is a mobile-first Progressive Web App (PWA) designed to simplify street parking in San Francisco. It provides accurate, real-time parking eligibility for the Mission and SOMA neighborhoods.

## Key Features

- **Interactive Map:** Displays parking legality for all blockfaces within the Mission & SOMA.
- **Dynamic Data Fetching:** Automatically fetches parking regulations based on the visible map area.
- **Duration Slider:** Intuitive "pill" slider to check parking legality for specific durations (1h - 24h).
- **Resident Focused:** Designed for SF residents running errands or visiting friends.
- **PWA Support:** Installable on mobile devices with offline capabilities.

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
