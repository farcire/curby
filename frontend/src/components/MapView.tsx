import { useMemo, useEffect } from 'react';
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

  useEffect(() => {
    const handleClick = (e: L.LeafletMouseEvent) => {
      const clickedPoint = e.latlng;
      
      let closestBlockface: Blockface | null = null;
      let minDistance = Infinity;

      blockfaces.forEach((blockface) => {
        const coords = blockface.geometry.coordinates;
        coords.forEach(([lng, lat]) => {
          const distance = clickedPoint.distanceTo(L.latLng(lat, lng));
          if (distance < minDistance && distance < 50) {
            minDistance = distance;
            closestBlockface = blockface;
          }
        });
      });

      if (closestBlockface) {
        const result = evaluateLegality(closestBlockface, checkTime, durationMinutes);
        onBlockfaceClick(closestBlockface, result);
      }
    };

    map.on('click', handleClick);

    return () => {
      map.off('click', handleClick);
    };
  }, [map, blockfaces, checkTime, durationMinutes, onBlockfaceClick]);

  return null;
}

export function MapView({ checkTime, durationMinutes, onBlockfaceClick, blockfaces }: MapViewProps) {
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

  const styleFeature = (feature: any) => {
    return {
      color: feature.properties.color,
      weight: 8,
      opacity: 0.9,
    };
  };

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

    layer.bindTooltip(feature.properties.streetName, {
      permanent: false,
      direction: 'top',
    });
  };

  return (
    <MapContainer
      center={[37.7527, -122.4078]}
      zoom={16}
      style={{ width: '100%', height: '100%' }}
      zoomControl={true}
      scrollWheelZoom={true}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      
      <GeoJSON
        key={JSON.stringify(geojsonData)}
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
  );
}