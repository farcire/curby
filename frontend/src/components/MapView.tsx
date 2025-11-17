import { useEffect, useRef, useState } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import { Blockface, LegalityResult } from '@/types/parking';
import { evaluateLegality, getStatusColor } from '@/utils/ruleEngine';

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

  useEffect(() => {
    if (!mapContainer.current) return;
    if (map.current) return;

    if (!MAPBOX_TOKEN) {
      setMapError('Mapbox token not configured. Please add VITE_MAPBOX_TOKEN to .env.local');
      setIsInitializing(false);
      return;
    }

    if (!MAPBOX_TOKEN.startsWith('pk.')) {
      setMapError('Invalid Mapbox token format. Token should start with "pk."');
      setIsInitializing(false);
      return;
    }

    mapboxgl.accessToken = MAPBOX_TOKEN;

    try {
      map.current = new mapboxgl.Map({
        container: mapContainer.current,
        style: 'mapbox://styles/mapbox/streets-v12',
        center: [-122.4078, 37.7527],
        zoom: 16,
        pitch: 0,
      });

      map.current.on('load', () => {
        setMapLoaded(true);
        setMapError(null);
        setIsInitializing(false);
      });

      map.current.on('error', (e) => {
        console.error('Mapbox error:', e);
        setMapError(`Map error: ${e.error?.message || 'Unknown error'}`);
        setIsInitializing(false);
      });

      map.current.addControl(new mapboxgl.NavigationControl(), 'top-right');
      map.current.addControl(
        new mapboxgl.GeolocateControl({
          positionOptions: {
            enableHighAccuracy: true,
          },
          trackUserLocation: true,
        }),
        'top-right'
      );

    } catch (error) {
      console.error('Error initializing map:', error);
      setMapError(`Failed to initialize map: ${error instanceof Error ? error.message : 'Unknown error'}`);
      setIsInitializing(false);
    }

    return () => {
      if (map.current) {
        map.current.remove();
        map.current = null;
      }
    };
  }, []);

  useEffect(() => {
    if (!map.current || !mapLoaded) return;

    if (map.current.getLayer('blockfaces')) {
      map.current.removeLayer('blockfaces');
    }
    if (map.current.getSource('blockfaces')) {
      map.current.removeSource('blockfaces');
    }

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

    map.current.addSource('blockfaces', {
      type: 'geojson',
      data: {
        type: 'FeatureCollection',
        features,
      },
    });

    map.current.addLayer({
      id: 'blockfaces',
      type: 'line',
      source: 'blockfaces',
      paint: {
        'line-color': ['get', 'color'],
        'line-width': 10,
        'line-opacity': 0.95,
      },
    });

    map.current.on('click', 'blockfaces', (e) => {
      if (!e.features || e.features.length === 0) return;

      const feature = e.features[0];
      const blockfaceId = feature.properties?.id;
      const blockface = blockfaces.find((b) => b.id === blockfaceId);

      if (blockface) {
        const result = evaluateLegality(blockface, checkTime, durationMinutes);
        onBlockfaceClick(blockface, result);
      }
    });

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

  if (isInitializing) {
    return (
      <div className="w-full h-full bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 flex items-center justify-center">
        <div className="text-center">
          <div className="relative mb-6">
            <div className="animate-spin rounded-full h-16 w-16 border-4 border-purple-200 border-t-purple-600 mx-auto"></div>
            <span className="absolute inset-0 flex items-center justify-center text-2xl">🗺️</span>
          </div>
          <p className="text-base font-semibold text-gray-900 mb-2">Loading your map...</p>
          <p className="text-sm text-gray-600">✨ Getting everything ready ✨</p>
        </div>
      </div>
    );
  }

  if (mapError) {
    return (
      <div className="w-full h-full bg-gradient-to-br from-red-50 to-orange-50 flex items-center justify-center">
        <div className="text-center p-8 max-w-md">
          <div className="text-6xl mb-4">😅</div>
          <h3 className="text-xl font-bold text-gray-900 mb-3">Oops! Map took a wrong turn</h3>
          <p className="text-sm text-gray-600 mb-4">{mapError}</p>
          <div className="bg-white border-2 border-orange-200 rounded-2xl p-4 text-left">
            <p className="text-xs font-semibold text-orange-900 mb-2 flex items-center gap-2">
              <span>🔧</span>
              Quick fixes to try:
            </p>
            <ul className="text-xs text-orange-800 space-y-1 list-disc list-inside">
              <li>Check your browser console for clues</li>
              <li>Make sure your Mapbox token is valid</li>
              <li>Verify your .env.local file exists</li>
              <li>Try refreshing the page</li>
            </ul>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-full relative">
      <div 
        ref={mapContainer} 
        className="absolute inset-0" 
        style={{ width: '100%', height: '100%' }}
      />
      
      {/* Playful Legend */}
      {mapLoaded && (
        <div className="absolute bottom-6 left-6 bg-white rounded-2xl shadow-xl p-4 space-y-3 text-xs z-10 border-2 border-purple-200">
          <div className="font-bold text-gray-900 mb-3 flex items-center gap-2">
            <span className="text-lg">🎨</span>
            Color Guide
          </div>
          <div className="space-y-2">
            <div className="flex items-center gap-3">
              <div className="w-6 h-2 bg-green-600 rounded-full shadow-sm"></div>
              <span className="text-gray-700 font-medium">Perfect! Park here 🎉</span>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-6 h-2 bg-amber-600 rounded-full shadow-sm"></div>
              <span className="text-gray-700 font-medium">Maybe (check rules) ⚠️</span>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-6 h-2 bg-red-600 rounded-full shadow-sm"></div>
              <span className="text-gray-700 font-medium">Nope! Keep going 🚫</span>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-6 h-2 bg-gray-600 rounded-full shadow-sm"></div>
              <span className="text-gray-700 font-medium">Not sure yet 🤔</span>
            </div>
          </div>
        </div>
      )}

      {/* Fun Location Badge */}
      {mapLoaded && (
        <div className="absolute top-6 left-6 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-2xl shadow-xl px-4 py-3 text-sm font-semibold z-10 flex items-center gap-2">
          <span className="text-xl">📍</span>
          Bryant & 24th St
        </div>
      )}
    </div>
  );
}