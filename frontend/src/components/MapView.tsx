import { useMemo } from 'react';
import { MapContainer, TileLayer, GeoJSON, useMap } from 'react-leaflet';
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

// Component to handle map events
function MapEventHandler({ 
  blockfaces, 
  checkTime, 
  durationMinutes, 
  onBlockfaceClick 
}: MapViewProps) {
  const map = useMap();

  // Handle click events on the map
  useMemo(() => {
    map.on('click', (e: L.LeafletMouseEvent) => {
      const clickedPoint = e.latlng;
      
      // Find the closest blockface to the click
      let closestBlockface: Blockface | null = null;
      let minDistance = Infinity;

      blockfaces.forEach((blockface) => {
        const coords = blockface.geometry.coordinates;
        coords.forEach(([lng, lat]) => {
          const distance = clickedPoint.distanceTo(L.latLng(lat, lng));
          if (distance < minDistance && distance < 50) { // 50 meter threshold
            minDistance = distance;
            closestBlockface = blockface;
          }
        });
      });

      if (closestBlockface) {
        const result = evaluateLegality(closestBlockface, checkTime, durationMinutes);
        onBlockfaceClick(closestBlockface, result);
      }
    });

    return () => {
      map.off('click');
    };
  }, [map, blockfaces, checkTime, durationMinutes, onBlockfaceClick]);

  return null;
}

export function MapView({ checkTime, durationMinutes, onBlockfaceClick, blockfaces }: MapViewProps) {
  // Generate GeoJSON data with legality colors
  const geojsonData = useMemo(() => {
    const features = blockfaces.map((blockface) => {
      const result = evaluateLegality(blockface, checkTime, durationMinutes);
      return {
        type: 'Feature' as const,
        properties: {
          id: blockface.id,
          color: getStatusColor(result.status),
          streetName: blockface.streetName,
        },
        geometry: blockface.geometry,
      };
    });

    return {
      type: 'FeatureCollection' as const,
      features,
    };
  }, [blockfaces, checkTime, durationMinutes]);

  // Style function for GeoJSON features
  const styleFeature = (feature: any) => {
    return {
      color: feature.properties.color,
      weight: 8,
      opacity: 0.9,
    };
  };

  // Handle feature click
  const onEachFeature = (feature: any, layer: L.Layer) => {
    layer.on({
      click: () => {
        const blockface = blockfaces.find((b) => b.id === feature.properties.id);
        if (blockface) {
          const result = evaluateLegality(blockface, checkTime, durationMinutes);
          onBlockfaceClick(blockface, result);
        }
      },
      mouseover: (e: L.LeafletMouseEvent) => {
        const layer = e.target;
        layer.setStyle({
          weight: 12,
        });
      },
      mouseout: (e: L.LeafletMouseEvent) => {
        const layer = e.target;
        layer.setStyle({
          weight: 8,
        });
      },
    });

    // Add tooltip
    layer.bindTooltip(feature.properties.streetName, {
      permanent: false,
      direction: 'top',
    });
  };

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
        
        <GeoJSON
          data={geojsonData}
          style={styleFeature}
          onEachFeature={onEachFeature}
        />

        <MapEventHandler
          blockfaces={blockfaces}
          checkTime={checkTime}
          durationMinutes={durationMinutes}
          onBlockfaceClick={onBlockfaceClick}
        />
      </MapContainer>
    </div>
  );
}