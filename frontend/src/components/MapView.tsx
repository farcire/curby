import { useEffect, useRef, useState } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import { Blockface, LegalityResult } from '@/types/parking';
import { evaluateLegality, getStatusColor } from '@/utils/ruleEngine';

// Get Mapbox token from environment variable
const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN || '';

interface MapViewProps {
  checkTime: Date;
  durationMinutes: number;
  onBlockfaceClick: (blockface: Blockface, result: LegalityResult) => void;
  blockfaces: Blockface[];
}

export function MapView({ checkTime, durationMinutes, onBlockfaceClick, blockfaces }: MapViewProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const [mapLoaded, setMapLoaded] = useState(false);
  const [mapError, setMapError] = useState<string | null>(null);
  const [isInitializing, setIsInitializing] = useState(true);

  // Debug: Log component render
  console.log('🗺️ MapView component rendered');
  console.log('Token available:', !!MAPBOX_TOKEN);
  console.log('Token value:', MAPBOX_TOKEN.substring(0, 20) + '...');

  // Initialize map
  useEffect(() => {
    console.log('🔄 MapView useEffect running');
    console.log('mapContainer.current:', !!mapContainer.current);
    console.log('map.current:', !!map.current);

    if (!mapContainer.current) {
      console.error('❌ Map container ref is null!');
      return;
    }

    if (map.current) {
      console.log('✅ Map already initialized, skipping');
      return;
    }

    console.log('🚀 Starting map initialization...');

    // Check if token exists
    if (!MAPBOX_TOKEN) {
      console.error('❌ No Mapbox token found');
      setMapError('Mapbox token not configured. Please add VITE_MAPBOX_TOKEN to .env.local');
      setIsInitializing(false);
      return;
    }

    if (!MAPBOX_TOKEN.startsWith('pk.')) {
      console.error('❌ Invalid token format');
      setMapError('Invalid Mapbox token format. Token should start with "pk."');
      setIsInitializing(false);
      return;
    }

    console.log('✅ Token validated, setting accessToken');
    mapboxgl.accessToken = MAPBOX_TOKEN;

    try {
      console.log('📍 Creating map at Bryant & 24th...');
      
      map.current = new mapboxgl.Map({
        container: mapContainer.current,
        style: 'mapbox://styles/mapbox/streets-v12',
        center: [-122.4078, 37.7527],
        zoom: 16,
        pitch: 0,
      });

      console.log('✅ Map instance created');

      map.current.on('load', () => {
        console.log('🎉 Map loaded successfully!');
        setMapLoaded(true);
        setMapError(null);
        setIsInitializing(false);
      });

      map.current.on('error', (e) => {
        console.error('❌ Mapbox error:', e);
        setMapError(`Map error: ${e.error?.message || 'Unknown error'}`);
        setIsInitializing(false);
      });

      // Add navigation controls
      map.current.addControl(new mapboxgl.NavigationControl(), 'top-right');
      console.log('✅ Navigation controls added');

      // Add geolocate control
      map.current.addControl(
        new mapboxgl.GeolocateControl({
          positionOptions: {
            enableHighAccuracy: true,
          },
          trackUserLocation: true,
        }),
        'top-right'
      );
      console.log('✅ Geolocate control added');

    } catch (error) {
      console.error('❌ Error initializing map:', error);
      setMapError(`Failed to initialize map: ${error instanceof Error ? error.message : 'Unknown error'}`);
      setIsInitializing(false);
    }

    return () => {
      if (map.current) {
        console.log('🧹 Cleaning up map...');
        map.current.remove();
        map.current = null;
      }
    };
  }, []);

  // Update blockfaces when time/duration changes or blockfaces data changes
  useEffect(() => {
    if (!map.current || !mapLoaded) {
      console.log('⏸️ Skipping blockface update - map not ready');
      return;
    }

    console.log('🔄 Updating blockfaces on map...', blockfaces.length, 'blockfaces');

    // Remove existing layers and sources
    if (map.current.getLayer('blockfaces')) {
      map.current.removeLayer('blockfaces');
      console.log('🗑️ Removed old blockfaces layer');
    }
    if (map.current.getSource('blockfaces')) {
      map.current.removeSource('blockfaces');
      console.log('🗑️ Removed old blockfaces source');
    }

    // Evaluate legality for all blockfaces
    const features = blockfaces.map((blockface) => {
      const result = evaluateLegality(blockface, checkTime, durationMinutes);
      
      return {
        type: 'Feature' as const,
        properties: {
          id: blockface.id,
          streetName: blockface.streetName,
          status: result.status,
          color: getStatusColor(result.status),
        },
        geometry: blockface.geometry,
      };
    });

    console.log('✅ Created', features.length, 'features for map');

    // Add source
    map.current.addSource('blockfaces', {
      type: 'geojson',
      data: {
        type: 'FeatureCollection',
        features,
      },
    });
    console.log('✅ Added blockfaces source');

    // Add layer
    map.current.addLayer({
      id: 'blockfaces',
      type: 'line',
      source: 'blockfaces',
      paint: {
        'line-color': ['get', 'color'],
        'line-width': 8,
        'line-opacity': 0.9,
      },
    });
    console.log('✅ Added blockfaces layer');

    // Add click handler
    map.current.on('click', 'blockfaces', (e) => {
      if (!e.features || e.features.length === 0) return;

      const feature = e.features[0];
      const blockfaceId = feature.properties?.id;
      const blockface = blockfaces.find((b) => b.id === blockfaceId);

      if (blockface) {
        console.log('👆 Clicked blockface:', blockface.streetName);
        const result = evaluateLegality(blockface, checkTime, durationMinutes);
        onBlockfaceClick(blockface, result);
      }
    });

    // Change cursor on hover
    map.current.on('mouseenter', 'blockfaces', () => {
      if (map.current) {
        map.current.getCanvas().style.cursor = 'pointer';
      }
    });

    map.current.on('mouseleave', 'blockfaces', () => {
      if (map.current) {
        map.current.getCanvas().style.cursor = '';
      }
    });
  }, [mapLoaded, checkTime, durationMinutes, onBlockfaceClick, blockfaces]);

  // Show loading state
  if (isInitializing) {
    console.log('⏳ Showing loading state');
    return (
      <div className="w-full h-full bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-sm text-gray-600">Loading map...</p>
          <p className="text-xs text-gray-500 mt-2">Check console for details</p>
        </div>
      </div>
    );
  }

  // Show error message if map fails to load
  if (mapError) {
    console.log('❌ Showing error state:', mapError);
    return (
      <div className="w-full h-full bg-gray-100 flex items-center justify-center">
        <div className="text-center p-8 max-w-md">
          <div className="text-red-600 text-4xl mb-4">🗺️</div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Map Not Available</h3>
          <p className="text-sm text-gray-600 mb-4">{mapError}</p>
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-left">
            <p className="text-xs font-semibold text-blue-900 mb-2">Troubleshooting:</p>
            <ul className="text-xs text-blue-800 space-y-1 list-disc list-inside">
              <li>Check browser console for errors</li>
              <li>Verify Mapbox token is valid</li>
              <li>Ensure .env.local file exists</li>
              <li>Try restarting the app</li>
            </ul>
          </div>
        </div>
      </div>
    );
  }

  console.log('✅ Rendering map container');
  return (
    <div className="w-full h-full relative">
      <div 
        ref={mapContainer} 
        className="absolute inset-0" 
        style={{ width: '100%', height: '100%' }}
      />
      
      {/* Legend */}
      {mapLoaded && (
        <div className="absolute bottom-4 left-4 bg-white rounded-lg shadow-lg p-3 space-y-2 text-xs z-10">
          <div className="font-semibold text-gray-900 mb-2">Legend</div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-1 bg-green-600 rounded"></div>
            <span className="text-gray-700">Legal</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-1 bg-amber-600 rounded"></div>
            <span className="text-gray-700">Limited</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-1 bg-red-600 rounded"></div>
            <span className="text-gray-700">Illegal</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-1 bg-gray-600 rounded"></div>
            <span className="text-gray-700">No Data</span>
          </div>
        </div>
      )}

      {/* Demo Location Badge */}
      {mapLoaded && (
        <div className="absolute top-4 left-4 bg-blue-600 text-white rounded-lg shadow-lg px-3 py-2 text-xs z-10">
          📍 Bryant & 24th St
        </div>
      )}
    </div>
  );
}