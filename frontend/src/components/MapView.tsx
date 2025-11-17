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
  radiusBlocks: number;
  centerPoint: [number, number]; // [lat, lng]
}

interface BlockfaceWithResult {
  blockface: Blockface;
  result: LegalityResult;
  distance: number;
}

export function MapView({ 
  checkTime, 
  durationMinutes, 
  onBlockfaceClick, 
  blockfaces,
  radiusBlocks,
  centerPoint,
}: MapViewProps) {
  const mapRef = useRef<L.Map | null>(null);
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const layersRef = useRef<L.Polyline[]>([]);
  const radiusCircleRef = useRef<L.Circle | null>(null);

  // Calculate appropriate zoom level based on radius
  const getZoomForRadius = (blocks: number): number => {
    // Zoom levels to show the radius circle comfortably
    if (blocks <= 1) return 18;
    if (blocks <= 2) return 17;
    if (blocks <= 3) return 17;
    if (blocks <= 5) return 16;
    return 15; // 8 blocks
  };

  // Initialize map
  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return;

    const initialZoom = getZoomForRadius(radiusBlocks);

    const map = L.map(mapContainerRef.current, {
      center: centerPoint,
      zoom: initialZoom,
      zoomControl: true,
      minZoom: 15,
      maxZoom: 18,
    });

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    }).addTo(map);

    // Add center marker
    const centerMarker = L.marker(centerPoint, {
      icon: L.divIcon({
        className: 'custom-center-marker',
        html: '<div style="background: linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%); width: 20px; height: 20px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.3);"></div>',
        iconSize: [20, 20],
        iconAnchor: [10, 10],
      }),
    }).addTo(map);

    centerMarker.bindTooltip('📍 You are here', {
      permanent: false,
      direction: 'top',
      offset: [0, -15],
    });

    mapRef.current = map;

    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, [centerPoint]);

  // Update zoom when radius changes
  useEffect(() => {
    if (!mapRef.current) return;

    const targetZoom = getZoomForRadius(radiusBlocks);
    const currentZoom = mapRef.current.getZoom();

    // Only animate zoom if it's different
    if (currentZoom !== targetZoom) {
      mapRef.current.setView(centerPoint, targetZoom, {
        animate: true,
        duration: 0.5, // Smooth 0.5 second animation
      });
    }
  }, [radiusBlocks, centerPoint]);

  // Update radius circle
  useEffect(() => {
    if (!mapRef.current) return;

    // Remove old circle
    if (radiusCircleRef.current) {
      mapRef.current.removeLayer(radiusCircleRef.current);
    }

    // Add new circle
    const radiusMeters = radiusBlocks * 110;
    const circle = L.circle(centerPoint, {
      radius: radiusMeters,
      color: '#8b5cf6',
      fillColor: '#8b5cf6',
      fillOpacity: 0.05,
      weight: 2,
      opacity: 0.3,
      dashArray: '5, 10',
    }).addTo(mapRef.current);

    radiusCircleRef.current = circle;
  }, [radiusBlocks, centerPoint]);

  // Calculate distance between two points (Haversine formula)
  const calculateDistance = (lat1: number, lng1: number, lat2: number, lng2: number): number => {
    const R = 6371e3; // Earth's radius in meters
    const φ1 = (lat1 * Math.PI) / 180;
    const φ2 = (lat2 * Math.PI) / 180;
    const Δφ = ((lat2 - lat1) * Math.PI) / 180;
    const Δλ = ((lng2 - lng1) * Math.PI) / 180;

    const a =
      Math.sin(Δφ / 2) * Math.sin(Δφ / 2) +
      Math.cos(φ1) * Math.cos(φ2) * Math.sin(Δλ / 2) * Math.sin(Δλ / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

    return R * c;
  };

  // Get blockface center point
  const getBlockfaceCenter = (blockface: Blockface): [number, number] => {
    const coords = blockface.geometry.coordinates;
    const centerLat = coords.reduce((sum, c) => sum + c[1], 0) / coords.length;
    const centerLng = coords.reduce((sum, c) => sum + c[0], 0) / coords.length;
    return [centerLat, centerLng];
  };

  // Update blockfaces when data changes
  useEffect(() => {
    if (!mapRef.current) return;

    // Clear existing layers
    layersRef.current.forEach((layer) => {
      mapRef.current?.removeLayer(layer);
    });
    layersRef.current = [];

    const radiusMeters = radiusBlocks * 110;

    // Evaluate all blockfaces with distance
    const blockfacesWithResults: BlockfaceWithResult[] = blockfaces.map(blockface => {
      const [centerLat, centerLng] = getBlockfaceCenter(blockface);
      const distance = calculateDistance(centerPoint[0], centerPoint[1], centerLat, centerLng);
      
      return {
        blockface,
        result: evaluateLegality(blockface, checkTime, durationMinutes),
        distance,
      };
    });

    // Add blockfaces as polylines
    blockfacesWithResults.forEach(({ blockface, result, distance }) => {
      const isInRadius = distance <= radiusMeters;
      
      // Each blockface shows only its own status color
      const color = isInRadius ? getStatusColor(result.status) : '#d1d5db'; // gray-300 for out of radius

      // Convert coordinates to Leaflet format [lat, lng]
      const latlngs: [number, number][] = blockface.geometry.coordinates.map(
        ([lng, lat]) => [lat, lng]
      );

      const polyline = L.polyline(latlngs, {
        color: color,
        weight: 10,
        opacity: isInRadius ? 0.9 : 0.3,
      });

      // Add tooltip
      let statusEmoji = '';
      if (!isInRadius) {
        statusEmoji = '🚫 '; // Out of radius
      } else if (result.status === 'legal') {
        statusEmoji = '✅ ';
      } else if (result.status === 'illegal') {
        statusEmoji = '🚫 ';
      } else {
        statusEmoji = '🤔 ';
      }

      polyline.bindTooltip(
        isInRadius 
          ? statusEmoji + blockface.streetName 
          : `🚫 ${blockface.streetName} (outside radius)`,
        {
          permanent: false,
          direction: 'top',
        }
      );

      // Add click handler only for blocks in radius
      if (isInRadius) {
        polyline.on('click', () => {
          onBlockfaceClick(blockface, result);
        });

        // Add hover effects
        polyline.on('mouseover', () => {
          polyline.setStyle({ weight: 14 });
        });

        polyline.on('mouseout', () => {
          polyline.setStyle({ weight: 10 });
        });
      }

      polyline.addTo(mapRef.current!);
      layersRef.current.push(polyline);
    });
  }, [blockfaces, checkTime, durationMinutes, onBlockfaceClick, radiusBlocks, centerPoint]);

  return (
    <div 
      ref={mapContainerRef} 
      className="absolute inset-0 w-full h-full"
      style={{ zIndex: 0 }}
    />
  );
}