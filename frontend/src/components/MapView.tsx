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
  const map = useRef<mapboxgl.Map | null>(null);
  const [mapLoaded, setMapLoaded] = useState(false);
  const [mapError, setMapError] = useState<string | null>(null);
  const [isInitializing, setIsInitializing] = useState(true);
  const [container, setContainer] = useState<HTMLDivElement | null>(null);

  console.log('🎬 MapView render - container:', !!container, 'map:', !!map.current, 'loaded:', mapLoaded);

  // Callback ref to get the container element
  const mapContainerRef = useCallback((node: HTMLDivElement | null) => {
    console.log('📦 mapContainerRef callback fired - node:', !!node);
    if (node) {
      console.log('✅ Setting container ref');
      setContainer(node);
    }
  }, []);

  // Check token on mount
  useEffect(() => {
    console.log('🔑 Checking Mapbox token...');
    console.log('Token exists:', !!MAPBOX_TOKEN);
    console.log('Token starts with pk.:', MAPBOX_TOKEN.startsWith('pk.'));
    console.log('Token length:', MAPBOX_TOKEN.length);
    
    if (!MAPBOX_TOKEN) {
      console.error('❌ No MAPBOX_TOKEN found in environment');
      setMapError('Mapbox token not configured. Add VITE_MAPBOX_TOKEN to your .env.local file');
      setIsInitializing(false);
    } else if (!MAPBOX_TOKEN.startsWith('pk.')) {
      console.error('❌ Invalid token format');
      setMapError('Invalid Mapbox token format');
      setIsInitializing(false);
    }
  }, []);

  // Initialize map when container is available
  useEffect(() => {
    console.log('🔄 Map init effect - container:', !!container, 'map:', !!map.current);
    
    if (!container) {
      console.log('⏳ No container yet, waiting...');
      return;
    }
    
    if (map.current) {
      console.log('✅ Map already exists, skipping init');
      return;
    }

    if (!MAPBOX_TOKEN || !MAPBOX_TOKEN.startsWith('pk.')) {
      console.log('❌ Invalid token, skipping init');
      return;
    }

    console.log('🚀 Starting map initialization...');
    mapboxgl.accessToken = MAPBOX_TOKEN;

    try {
      console.log('📍 Creating Mapbox instance...');
      map.current = new mapboxgl.Map({
        container: container,
        style: 'mapbox://styles/mapbox/streets-v12',
        center: [-122.4078, 37.7527],
        zoom: 16,
      });

      console.log('✅ Map instance created, waiting for load event...');

      map.current.on('load', () => {
        console.log('🎉 Map loaded successfully!');
        setMapLoaded(true);
        setMapError(null);
        setIsInitializing(false);
      });

      map.current.on('error', (e) => {
        console.error('❌ Map error event:', e);
        setMapError(e.error?.message || 'Map error');
        setIsInitializing(false);
      });

      // Add controls
      console.log('🎮 Adding map controls...');
      map.current.addControl(new mapboxgl.NavigationControl(), 'top-right');
      map.current.addControl(
        new mapboxgl.GeolocateControl({
          positionOptions: { enableHighAccuracy: true },
          trackUserLocation: true,
        }),
        'top-right'
      );
      console.log('✅ Controls added');

    } catch (error) {
      console.error('❌ Exception during map init:', error);
      setMapError(error instanceof Error ? error.message : 'Unknown error');
      setIsInitializing(false);
    }

    return () => {
      console.log('🧹 Cleanup - removing map');
      if (map.current) {
        map.current.remove();
        map.current = null;
      }
    };
  }, [container]);

  // Update blockfaces
  useEffect(() => {
    if (!map.current || !mapLoaded) {
      console.log('⏭️ Skipping blockface update - map not ready');
      return;
    }

    console.log('🔄 Updating blockfaces:', blockfaces.length);

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
      data: { type: 'FeatureCollection', features },
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
      if (map.current) map.current.getCanvas().style.cursor = 'pointer';
    });
    map.current.on('mouseleave', 'blockfaces', () => {
      if (map.current) map.current.getCanvas().style.cursor = '';
    });

    console.log('✅ Blockfaces updated');
  }, [mapLoaded, checkTime, durationMinutes, onBlockfaceClick, blockfaces]);

  console.log('🎨 Rendering - initializing:', isInitializing, 'error:', !!mapError, 'loaded:', mapLoaded);

  if (isInitializing) {
    return (
      <div className="w-full h-full bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-sm text-gray-600">Loading map...</p>
          <p className="text-xs text-gray-400 mt-2">Check console for details</p>
        </div>
      </div>
    );
  }

  if (mapError) {
    return (
      <div className="w-full h-full bg-gray-100 flex items-center justify-center">
        <div className="text-center p-8 max-w-md">
          <div className="text-red-600 text-4xl mb-4">🗺️</div>
          <h3 className="text-lg font-semibold mb-2">Map Not Available</h3>
          <p className="text-sm text-gray-600 mb-4">{mapError}</p>
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 text-left text-xs">
            <p className="font-semibold mb-2">To fix this:</p>
            <ol className="list-decimal list-inside space-y-1">
              <li>Create a .env.local file in your project root</li>
              <li>Add: VITE_MAPBOX_TOKEN=pk.your_token_here</li>
              <li>Get a token from mapbox.com</li>
              <li>Restart the dev server</li>
            </ol>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-full relative">
      <div 
        ref={mapContainerRef} 
        className="absolute inset-0 w-full h-full bg-gray-200"
        style={{ minHeight: '100%', minWidth: '100%' }}
      />
      
      {mapLoaded && (
        <>
          <div className="absolute bottom-4 left-4 bg-white rounded-lg shadow-lg p-3 space-y-2 text-xs z-10">
            <div className="font-semibold mb-2">Legend</div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-1 bg-green-600 rounded"></div>
              <span>Legal</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-1 bg-red-600 rounded"></div>
              <span>Illegal</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-1 bg-gray-600 rounded"></div>
              <span>No Data</span>
            </div>
          </div>
          <div className="absolute top-4 left-4 bg-blue-600 text-white rounded-lg shadow-lg px-3 py-2 text-xs z-10">
            📍 Bryant & 24th St
          </div>
        </>
      )}
    </div>
  );
}