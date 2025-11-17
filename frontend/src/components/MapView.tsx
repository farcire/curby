import { useEffect } from 'react';
import { MapContainer, TileLayer, useMap } from 'react-leaflet';
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

// Component to render blockfaces as Leaflet layers
function BlockfaceLayer({ 
  blockfaces, 
  checkTime, 
  durationMinutes, 
  onBlockfaceClick 
}: MapViewProps) {
  const map = useMap();

  useEffect(() => {
    // Clear existing layers
    map.eachLayer((layer) => {
      if (layer instanceof L.Polyline && !(layer instanceof L.TileLayer)) {
        map.removeLayer(layer);
      }
    });

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

      polyline.addTo(map);
    });

    // Cleanup on unmount
    return () => {
      map.eachLayer((layer) => {
        if (layer instanceof L.Polyline && !(layer instanceof L.TileLayer)) {
          map.removeLayer(layer);
        }
      });
    };
  }, [map, blockfaces, checkTime, durationMinutes, onBlockfaceClick]);

  return null;
}

export function MapView({ checkTime, durationMinutes, onBlockfaceClick, blockfaces }: MapViewProps) {
  return (
    <div className="absolute inset-0 w-full h-full">
      <MapContainer
        center={[37.7527, -122.4078]}
        zoom={16}
        style={{ width: '100%', height: '100%' }}
        zoomControl={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        
        <BlockfaceLayer
          blockfaces={blockfaces}
          checkTime={checkTime}
          durationMinutes={durationMinutes}
          onBlockfaceClick={onBlockfaceClick}
        />
      </MapContainer>
    </div>
  );
}