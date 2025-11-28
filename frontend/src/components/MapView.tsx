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
  centerPoint: [number, number]; // [lat, lng]
  onMapMove?: (bounds: L.LatLngBounds) => void;
}

interface BlockfaceWithResult {
  blockface: Blockface;
  result: LegalityResult;
}

// Mission District Approximate Bounds
const MISSION_BOUNDS = L.latLngBounds(
  [37.747, -122.427], // SW (Cesar Chavez & Guerreroish)
  [37.773, -122.403]  // NE (13th/Duboce & Potreroish)
);

export function MapView({
  checkTime,
  durationMinutes,
  onBlockfaceClick,
  blockfaces,
  centerPoint,
  onMapMove,
}: MapViewProps) {
  const mapRef = useRef<L.Map | null>(null);
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const layersRef = useRef<L.Polyline[]>([]);

  // Initialize map
  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return;

    // Initial zoom ~17 is roughly 3 blocks radius view
    const initialZoom = 17;

    const map = L.map(mapContainerRef.current, {
      center: centerPoint,
      zoom: initialZoom,
      zoomControl: true,
      minZoom: 14,
      maxZoom: 18,
      maxBounds: MISSION_BOUNDS, // Restrict to Mission District
      maxBoundsViscosity: 0.8,
    });

    // Notify parent of initial bounds
    if (onMapMove) {
      onMapMove(map.getBounds());
    }

    map.on('moveend', () => {
      if (onMapMove) {
        onMapMove(map.getBounds());
      }
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
  }, [centerPoint]); // Re-initialize if center point deeply changes (usually it won't)

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

    // Evaluate all blockfaces
    const blockfacesWithResults: BlockfaceWithResult[] = blockfaces.map(blockface => {
      return {
        blockface,
        result: evaluateLegality(blockface, checkTime, durationMinutes),
      };
    });

    // Add blockfaces as polylines
    blockfacesWithResults.forEach(({ blockface, result }) => {
      const color = getStatusColor(result.status);

      // Use exact coordinates from backend (geometry is already side-specific)
      const latlngs: [number, number][] = blockface.geometry.coordinates.map(
        ([lng, lat]) => [lat, lng]
      );

      const polyline = L.polyline(latlngs, {
        color: color,
        weight: 8, // Slightly thinner
        opacity: 0.6, // More transparent as requested (was 0.9)
        className: 'hover:opacity-100 transition-opacity duration-200',
      });

      // Add tooltip
      let statusEmoji = '';
      if (result.status === 'legal') {
        statusEmoji = '✅ ';
      } else if (result.status === 'illegal') {
        statusEmoji = '🚫 ';
      } else {
        statusEmoji = '🤔 ';
      }

      polyline.bindTooltip(
        statusEmoji + blockface.streetName,
        {
          permanent: false,
          direction: 'top',
        }
      );

      polyline.on('click', () => {
        onBlockfaceClick(blockface, result);
      });

      // Add hover effects
      polyline.on('mouseover', () => {
        polyline.setStyle({
            weight: 12,
            opacity: 1.0
        });
      });

      polyline.on('mouseout', () => {
        polyline.setStyle({
            weight: 8,
            opacity: 0.6
        });
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