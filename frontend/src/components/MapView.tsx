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

  const mapContainerRef = useCallback((node: HTMLDivElement | null) => {
    if (node) {
      console.log('🗺️ Map container ref set:', node);
      setContainer(node);
    }
  }, []);

  useEffect(() => {
    console.log('🔑 Mapbox token check:', {
      hasToken: !!MAPBOX_TOKEN,
      tokenLength: MAPBOX_TOKEN.length,
      tokenStart: MAPBOX_TOKEN.substring(0, 10),
      isValidFormat: MAPBOX_TOKEN.startsWith('pk.'),
    });

    if (!MAPBOX_TOKEN) {
      setMapError('Mapbox token not configured. Please add VITE_MAPBOX_TOKEN to your .env.local file and restart the server.');
      setIsInitializing(false);
    } else if (!MAPBOX_TOKEN.startsWith('pk.')) {
      setMapError('Your Mapbox token is invalid. It should start with "pk.". Please check your .env.local file.');
      setIsInitializing(false);
    }
  }, []);

  useEffect(() => {
    console.log('🚀 Map initialization effect:', {
      hasContainer: !!container,
      hasError: !!mapError,
      hasExistingMap: !!map.current,
    });

    if (!container || mapError || map.current) {
      return;
    }

    console.log('🎯 Setting Mapbox access token and creating map...');
    mapboxgl.accessToken = MAPBOX_TOKEN;

    try {
      console.log('🏗️ Creating new Mapbox map instance...');
      const newMap = new mapboxgl.Map({
        container: container,
        style: 'mapbox://styles/mapbox/streets-v12',
        center: [-122.4078, 37.7527],
        zoom: 16,
      });

      console.log('📡 Map instance created, waiting for load event...');

      newMap.on('load', () => {
        console.log('✅ Map loaded successfully!');
        map.current = newMap;
        setMapLoaded(true);
        setIsInitializing(false);
      });

      newMap.on('error', (e) => {
        console.error('❌ Map error:', e);
        setMapError(e.error?.message || 'An unknown error occurred while loading the map.');
        setIsInitializing(false);
      });

      newMap.on('styledata', () => {
        console.log('🎨 Map style loaded');
      });

      newMap.on('sourcedata', (e) => {
        console.log('📊 Map source data:', e.sourceId, e.isSourceLoaded);
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

    return () => {
      console.log('🧹 Cleaning up map...');
      if (map.current) {
        map.current.remove();
        map.current = null;
      }
    };
  }, [container, mapError]);

  useEffect(() => {
    console.log('🔄 Blockfaces update effect:', {
      hasMap: !!map.current,
      mapLoaded,
      blockfaceCount: blockfaces.length,
    });

    if (!map.current || !mapLoaded) {
      return;
    }

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

    console.log('📍 Adding/updating blockfaces:', features.length, 'features');

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
            console.log('🖱️ Blockface clicked:', e.features?.[0]?.properties?.id);
            if (!e.features?.length) return;
            const blockfaceId = e.features[0].properties?.id;
            const blockface = blockfaces.find((b) => b.id === blockfaceId);
            if (blockface) {
                onBlockfaceClick(blockface, evaluateLegality(blockface, checkTime, durationMinutes));
            }
        });

        map.current.on('mouseenter', 'blockfaces', () => map.current!.getCanvas().style.cursor = 'pointer');
        map.current.on('mouseleave', 'blockfaces', () => map.current!.getCanvas().style.cursor = '');
    }
  }, [mapLoaded, checkTime, durationMinutes, blockfaces, onBlockfaceClick]);

  if (isInitializing) {
    return (
      <div className="w-full h-full bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto mb-4"></div>
          <p className="text-sm text-gray-600">Loading map...</p>
          <p className="text-xs text-gray-500 mt-2">Check console for details</p>
        </div>
      </div>
    );
  }

  if (mapError) {
    return (
      <div className="w-full h-full bg-red-50 flex items-center justify-center p-4">
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
    <div className="w-full h-full relative">
      <div 
        ref={mapContainerRef} 
        className="absolute inset-0 w-full h-full bg-gray-200"
      />
      {!mapLoaded && (
        <div className="absolute inset-0 bg-white/80 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600 mx-auto mb-2"></div>
            <p className="text-xs text-gray-600">Rendering map...</p>
          </div>
        </div>
      )}
    </div>
  );
}