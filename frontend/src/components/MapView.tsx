import { useEffect, useRef, useState, useCallback } from 'react';
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
  const mapContainer = useRef<HTMLDivElement | null>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const [mapLoaded, setMapLoaded] = useState(false);
  const [mapError, setMapError] = useState<string | null>(null);
  const [isInitializing, setIsInitializing] = useState(true);
  const [containerReady, setContainerReady] = useState(false);

  // Callback ref to ensure container is mounted
  const setMapContainer = useCallback((node: HTMLDivElement | null) => {
    if (node) {
      console.log('📦 Container mounted with dimensions:', {
        width: node.offsetWidth,
        height: node.offsetHeight,
      });
      mapContainer.current = node;
      setContainerReady(true);
    }
  }, []);

  // Initialize map only after container is ready
  useEffect(() => {
    if (!containerReady) {
      console.log('⏳ Waiting for container to be ready...');
      return;
    }

    console.log('🎬 MapView useEffect triggered');
    console.log('🔑 Mapbox token check:', {
      hasToken: !!MAPBOX_TOKEN,
      tokenLength: MAPBOX_TOKEN.length,
      tokenStart: MAPBOX_TOKEN.substring(0, 10),
      isValidFormat: MAPBOX_TOKEN.startsWith('pk.'),
    });

    if (!MAPBOX_TOKEN) {
      console.error('❌ No Mapbox token');
      setMapError('Mapbox token not configured. Please add VITE_MAPBOX_TOKEN to your .env.local file and restart the server.');
      setIsInitializing(false);
      return;
    }
    
    if (!MAPBOX_TOKEN.startsWith('pk.')) {
      console.error('❌ Invalid Mapbox token format');
      setMapError('Your Mapbox token is invalid. It should start with "pk.". Please check your .env.local file.');
      setIsInitializing(false);
      return;
    }

    if (!mapContainer.current) {
      console.error('❌ Map container not available');
      return;
    }

    if (map.current) {
      console.log('⚠️ Map already exists, skipping initialization');
      return;
    }

    console.log('🏗️ Starting map initialization...');

    mapboxgl.accessToken = MAPBOX_TOKEN;

    try {
      console.log('🎯 Creating Mapbox map instance...');
      const newMap = new mapboxgl.Map({
        container: mapContainer.current,
        style: 'mapbox://styles/mapbox/streets-v12',
        center: [-122.4078, 37.7527],
        zoom: 16,
      });

      console.log('✅ Map instance created, waiting for load event...');

      newMap.on('load', () => {
        console.log('🎉 Map loaded successfully!');
        map.current = newMap;
        setMapLoaded(true);
        setIsInitializing(false);
      });

      newMap.on('error', (e) => {
        console.error('❌ Map error:', e);
        setMapError(e.error?.message || 'An unknown error occurred while loading the map.');
        setIsInitializing(false);
      });

      newMap.addControl(new mapboxgl.NavigationControl(), 'top-right');
      newMap.addControl(
        new mapboxgl.GeolocateControl({
          positionOptions: { enableHighAccuracy: true },
          trackUserLocation: true,
        }),
        'top-right'
      );
    } catch (error) {
      console.error('💥 Error creating map:', error);
      setMapError(error instanceof Error ? error.message : 'An unexpected error occurred.');
      setIsInitializing(false);
    }
  }, [containerReady]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      console.log('🧹 Cleaning up map...');
      if (map.current) {
        map.current.remove();
        map.current = null;
      }
    };
  }, []);

  // Update blockfaces on map
  useEffect(() => {
    if (!map.current || !mapLoaded) {
      console.log('⏳ Waiting for map to load before updating blockfaces');
      return;
    }

    console.log('🔄 Updating blockfaces on map...');

    const source = map.current.getSource('blockfaces');
    const features = blockfaces.map((blockface) => {
      const result = evaluateLegality(blockface, checkTime, durationMinutes);
      return {
        type: 'Feature' as const,
        properties: {
          id: blockface.id,
          color: getStatusColor(result.status),
        },
        geometry: blockface.geometry,
      };
    });
    const geojsonData = { type: 'FeatureCollection' as const, features };

    console.log('📍 Updating blockfaces:', features.length, 'features');

    if (source) {
      console.log('🔄 Updating existing source');
      (source as mapboxgl.GeoJSONSource).setData(geojsonData);
    } else {
      console.log('➕ Adding new source and layer');
      map.current.addSource('blockfaces', {
        type: 'geojson',
        data: geojsonData,
      });

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

      map.current.on('click', 'blockfaces', (e) => {
        if (!e.features?.length) return;
        const blockfaceId = e.features[0].properties?.id;
        const blockface = blockfaces.find((b) => b.id === blockfaceId);
        if (blockface) {
          onBlockfaceClick(blockface, evaluateLegality(blockface, checkTime, durationMinutes));
        }
      });

      map.current.on('mouseenter', 'blockfaces', () => {
        map.current!.getCanvas().style.cursor = 'pointer';
      });
      map.current.on('mouseleave', 'blockfaces', () => {
        map.current!.getCanvas().style.cursor = '';
      });
    }
  }, [mapLoaded, checkTime, durationMinutes, blockfaces, onBlockfaceClick]);

  if (isInitializing) {
    return (
      <div className="absolute inset-0 bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto mb-4"></div>
          <p className="text-sm text-gray-600">Loading map...</p>
          <p className="text-xs text-gray-500 mt-2">Initializing Mapbox...</p>
        </div>
      </div>
    );
  }

  if (mapError) {
    return (
      <div className="absolute inset-0 bg-red-50 flex items-center justify-center p-4">
        <div className="text-center bg-white p-6 rounded-2xl shadow-lg border-2 border-red-200 max-w-md">
          <div className="text-5xl mb-3">🗺️💥</div>
          <h3 className="text-lg font-bold text-red-800 mb-2">Map Loading Error</h3>
          <p className="text-sm text-gray-700 mb-4">{mapError}</p>
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 text-left text-xs text-yellow-900">
            <p className="font-semibold mb-2">How to fix:</p>
            <ol className="list-decimal list-inside space-y-1">
              <li>Create a file named `.env.local` in the project root.</li>
              <li>Add your Mapbox token: `VITE_MAPBOX_TOKEN=pk.your_token_here`</li>
              <li>Get a free token from `mapbox.com`.</li>
              <li>Restart the application server.</li>
            </ol>
          </div>
          <p className="text-xs text-gray-500 mt-3">Check browser console for more details</p>
        </div>
      </div>
    );
  }

  return (
    <div 
      ref={setMapContainer}
      className="absolute inset-0 w-full h-full bg-gray-200" 
      style={{ minHeight: '400px' }}
    />
  );
}