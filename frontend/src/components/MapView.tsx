import { useEffect, useRef, useState } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import { Blockface, LegalityResult } from '@/types/parking';
import { evaluateLegality, getStatusColor } from '@/utils/ruleEngine';
import { mockBlockfaces } from '@/data/mockBlockfaces';

// Note: In production, use environment variable
const MAPBOX_TOKEN = 'pk.eyJ1IjoiY3VyYnktZGVtbyIsImEiOiJjbTBkZW1vMTIzNDU2In0.demo_token_replace_in_production';

interface MapViewProps {
  checkTime: Date;
  durationMinutes: number;
  onBlockfaceClick: (blockface: Blockface, result: LegalityResult) => void;
}

export function MapView({ checkTime, durationMinutes, onBlockfaceClick }: MapViewProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const [mapLoaded, setMapLoaded] = useState(false);

  // Initialize map
  useEffect(() => {
    if (!mapContainer.current || map.current) return;

    mapboxgl.accessToken = MAPBOX_TOKEN;

    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/streets-v12',
      center: [-122.4078, 37.7527], // Bryant & 24th intersection
      zoom: 16, // Closer zoom for demo
      pitch: 0,
    });

    map.current.on('load', () => {
      setMapLoaded(true);
    });

    // Add navigation controls
    map.current.addControl(new mapboxgl.NavigationControl(), 'top-right');

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

    return () => {
      map.current?.remove();
      map.current = null;
    };
  }, []);

  // Update blockfaces when time/duration changes
  useEffect(() => {
    if (!map.current || !mapLoaded) return;

    // Remove existing layers and sources
    if (map.current.getLayer('blockfaces')) {
      map.current.removeLayer('blockfaces');
    }
    if (map.current.getSource('blockfaces')) {
      map.current.removeSource('blockfaces');
    }

    // Evaluate legality for all blockfaces
    const features = mockBlockfaces.map((blockface) => {
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

    // Add source
    map.current.addSource('blockfaces', {
      type: 'geojson',
      data: {
        type: 'FeatureCollection',
        features,
      },
    });

    // Add layer
    map.current.addLayer({
      id: 'blockfaces',
      type: 'line',
      source: 'blockfaces',
      paint: {
        'line-color': ['get', 'color'],
        'line-width': 8, // Thicker for demo visibility
        'line-opacity': 0.9,
      },
    });

    // Add click handler
    map.current.on('click', 'blockfaces', (e) => {
      if (!e.features || e.features.length === 0) return;

      const feature = e.features[0];
      const blockfaceId = feature.properties?.id;
      const blockface = mockBlockfaces.find((b) => b.id === blockfaceId);

      if (blockface) {
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
  }, [mapLoaded, checkTime, durationMinutes, onBlockfaceClick]);

  return (
    <div className="relative w-full h-full">
      <div ref={mapContainer} className="absolute inset-0" />
      
      {/* Legend */}
      <div className="absolute bottom-4 left-4 bg-white rounded-lg shadow-lg p-3 space-y-2 text-xs">
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

      {/* Demo Location Badge */}
      <div className="absolute top-4 left-4 bg-blue-600 text-white rounded-lg shadow-lg px-3 py-2 text-xs">
        📍 Bryant & 24th St
      </div>
    </div>
  );
}