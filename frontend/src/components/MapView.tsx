import { useState, useCallback, useMemo } from 'react';
import Map, { Source, Layer, MapLayerMouseEvent } from 'react-map-gl';
import type { LayerProps } from 'react-map-gl';
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
  const [cursor, setCursor] = useState<string>('auto');

  // Generate GeoJSON data with legality colors
  const geojsonData = useMemo(() => {
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

    return {
      type: 'FeatureCollection' as const,
      features,
    };
  }, [blockfaces, checkTime, durationMinutes]);

  // Layer style for blockfaces
  const blockfaceLayer: LayerProps = {
    id: 'blockfaces',
    type: 'line',
    paint: {
      'line-color': ['get', 'color'],
      'line-width': 8,
      'line-opacity': 0.9,
    },
  };

  // Handle click on blockface
  const handleClick = useCallback(
    (event: MapLayerMouseEvent) => {
      const feature = event.features?.[0];
      if (!feature) return;

      const blockfaceId = feature.properties?.id;
      const blockface = blockfaces.find((b) => b.id === blockfaceId);
      
      if (blockface) {
        const result = evaluateLegality(blockface, checkTime, durationMinutes);
        onBlockfaceClick(blockface, result);
      }
    },
    [blockfaces, checkTime, durationMinutes, onBlockfaceClick]
  );

  // Handle mouse enter/leave for cursor
  const onMouseEnter = useCallback(() => setCursor('pointer'), []);
  const onMouseLeave = useCallback(() => setCursor('auto'), []);

  if (!MAPBOX_TOKEN) {
    return (
      <div className="absolute inset-0 bg-red-50 flex items-center justify-center p-4">
        <div className="text-center bg-white p-6 rounded-2xl shadow-lg border-2 border-red-200 max-w-md">
          <div className="text-5xl mb-3">🗺️💥</div>
          <h3 className="text-lg font-bold text-red-800 mb-2">Map Configuration Needed</h3>
          <p className="text-sm text-gray-700 mb-4">
            Mapbox token not configured. Please add VITE_MAPBOX_TOKEN to your .env.local file and restart the server.
          </p>
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 text-left text-xs text-yellow-900">
            <p className="font-semibold mb-2">How to fix:</p>
            <ol className="list-decimal list-inside space-y-1">
              <li>Create a file named `.env.local` in the project root</li>
              <li>Add: VITE_MAPBOX_TOKEN=pk.your_token_here</li>
              <li>Get a free token from mapbox.com</li>
              <li>Restart the dev server</li>
            </ol>
          </div>
        </div>
      </div>
    );
  }

  if (!MAPBOX_TOKEN.startsWith('pk.')) {
    return (
      <div className="absolute inset-0 bg-red-50 flex items-center justify-center p-4">
        <div className="text-center bg-white p-6 rounded-2xl shadow-lg border-2 border-red-200 max-w-md">
          <div className="text-5xl mb-3">🗺️💥</div>
          <h3 className="text-lg font-bold text-red-800 mb-2">Invalid Mapbox Token</h3>
          <p className="text-sm text-gray-700 mb-4">
            Your Mapbox token is invalid. It should start with "pk.". Please check your .env.local file.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="absolute inset-0 w-full h-full">
      <Map
        mapboxAccessToken={MAPBOX_TOKEN}
        initialViewState={{
          longitude: -122.4078,
          latitude: 37.7527,
          zoom: 16,
        }}
        style={{ width: '100%', height: '100%' }}
        mapStyle="mapbox://styles/mapbox/streets-v12"
        cursor={cursor}
        interactiveLayerIds={['blockfaces']}
        onClick={handleClick}
        onMouseEnter={onMouseEnter}
        onMouseLeave={onMouseLeave}
      >
        <Source id="blockfaces" type="geojson" data={geojsonData}>
          <Layer {...blockfaceLayer} />
        </Source>
      </Map>
    </div>
  );
}