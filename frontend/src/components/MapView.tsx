import { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { Blockface, LegalityResult } from '@/types/parking';
import { evaluateLegality, getStatusColor } from '@/utils/ruleEngine';

interface MapViewProps {
  checkTime: Date;
  durationMinutes: number;
  onBlockfaceClick: (blockface: Blockface, result: LegalityResult) => void;
  blockfaces: Blockface[];
}

export function MapView({ checkTime, durationMinutes, onBlockfaceClick, blockfaces }: MapViewProps) {
  const mapRef = useRef<L.Map | null>(null);
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const layersRef = useRef<L.Polyline[]>([]);

  // Initialize map
  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return;

    // Create map
    const map = L.map(mapContainerRef.current, {
      center: [37.7527, -122.4078],
      zoom: 16,
      zoomControl: true,
    });

    // Add tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    }).addTo(map);

    mapRef.current = map;

    // Cleanup
    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, []);

  // Update blockfaces when data changes
  useEffect(() => {
    if (!mapRef.current) return;

    // Clear existing layers
    layersRef.current.forEach((layer) => {
      mapRef.current?.removeLayer(layer);
    });
    layersRef.current = [];

    // Add blockfaces as polylines
    blockfaces.forEach((blockface) => {
      const result = evaluateLegality(blockface, checkTime, durationMinutes);
      const color = getStatusColor(result.status);

      // Convert coordinates to Leaflet format [lat, lng]
      const latlngs: [number, number][] = blockface.geometry.coordinates.map(
        ([lng, lat]) => [lat, lng]
      );

      const polyline = L.polyline(latlngs, {
        color,
        weight: 8,
        opacity: 0.9,
      });

      // Add tooltip
      polyline.bindTooltip(blockface.streetName, {
        permanent: false,
        direction: 'top',
      });

      // Add click handler
      polyline.on('click', () => {
        onBlockfaceClick(blockface, result);
      });

      // Add hover effects
      polyline.on('mouseover', () => {
        polyline.setStyle({ weight: 12 });
      });

      polyline.on('mouseout', () => {
        polyline.setStyle({ weight: 8 });
      });

      polyline.addTo(mapRef.current!);
      layersRef.current.push(polyline);
    });
  }, [blockfaces, checkTime, durationMinutes, onBlockfaceClick]);

  return (
    <div 
      ref={mapContainerRef} 
      className="absolute inset-0 w-full h-full"
      style={{ zIndex: 0 }}
    />
  );
}