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

interface BlockfaceWithResult {
  blockface: Blockface;
  result: LegalityResult;
}

export function MapView({ checkTime, durationMinutes, onBlockfaceClick, blockfaces }: MapViewProps) {
  const mapRef = useRef<L.Map | null>(null);
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const layersRef = useRef<L.Polyline[]>([]);

  // Initialize map centered on Bryant & 20th with 5-block radius view
  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return;

    // Create map centered on Bryant & 20th Street
    const map = L.map(mapContainerRef.current, {
      center: [37.75885, -122.40935], // Bryant & 20th
      zoom: 16, // Shows approximately 5-block radius
      zoomControl: true,
      minZoom: 14,
      maxZoom: 18,
    });

    // Add tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    }).addTo(map);

    // Add a subtle circle to show the 5-block radius area
    L.circle([37.75885, -122.40935], {
      radius: 550, // approximately 5 blocks (110m per block)
      color: '#8b5cf6',
      fillColor: '#8b5cf6',
      fillOpacity: 0.05,
      weight: 2,
      opacity: 0.3,
      dashArray: '5, 10',
    }).addTo(map);

    // Add a marker at Bryant & 20th
    const centerMarker = L.marker([37.75885, -122.40935], {
      icon: L.divIcon({
        className: 'custom-center-marker',
        html: '<div style="background: linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%); width: 16px; height: 16px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.3);"></div>',
        iconSize: [16, 16],
        iconAnchor: [8, 8],
      }),
    }).addTo(map);

    centerMarker.bindTooltip('Bryant & 20th', {
      permanent: false,
      direction: 'top',
      offset: [0, -10],
    });

    mapRef.current = map;

    // Cleanup
    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, []);

  // Helper function to get street segment key (street name + approximate block)
  const getStreetSegmentKey = (blockface: Blockface): string => {
    // Get average lat/lng to identify the block
    const coords = blockface.geometry.coordinates;
    const avgLat = coords.reduce((sum, c) => sum + c[1], 0) / coords.length;
    const avgLng = coords.reduce((sum, c) => sum + c[0], 0) / coords.length;
    
    // Round to 3 decimal places to group nearby segments
    const latKey = Math.round(avgLat * 1000);
    const lngKey = Math.round(avgLng * 1000);
    
    return `${blockface.streetName}-${latKey}-${lngKey}`;
  };

  // Helper function to determine color based on opposite sides
  const getBlockfaceColor = (
    blockface: Blockface,
    result: LegalityResult,
    allBlockfacesWithResults: BlockfaceWithResult[]
  ): string => {
    // Find blockfaces on the same street segment
    const segmentKey = getStreetSegmentKey(blockface);
    const sameSegment = allBlockfacesWithResults.filter(
      bwr => getStreetSegmentKey(bwr.blockface) === segmentKey
    );

    // If we only have one side, use normal color
    if (sameSegment.length === 1) {
      return getStatusColor(result.status);
    }

    // Check if opposite sides have different legality
    const hasLegal = sameSegment.some(bwr => bwr.result.status === 'legal');
    const hasIllegal = sameSegment.some(
      bwr => bwr.result.status === 'illegal' || bwr.result.status === 'insufficient-data'
    );

    // If one side is legal and the other is not, show yellow
    if (hasLegal && hasIllegal) {
      return '#eab308'; // yellow-500
    }

    // Otherwise, use the normal color for this blockface
    return getStatusColor(result.status);
  };

  // Update blockfaces when data changes
  useEffect(() => {
    if (!mapRef.current) return;

    // Clear existing layers
    layersRef.current.forEach((layer) => {
      mapRef.current?.removeLayer(layer);
    });
    layersRef.current = [];

    // Evaluate all blockfaces first
    const blockfacesWithResults: BlockfaceWithResult[] = blockfaces.map(blockface => ({
      blockface,
      result: evaluateLegality(blockface, checkTime, durationMinutes),
    }));

    // Add blockfaces as polylines
    blockfacesWithResults.forEach(({ blockface, result }) => {
      const color = getBlockfaceColor(blockface, result, blockfacesWithResults);

      // Convert coordinates to Leaflet format [lat, lng]
      const latlngs: [number, number][] = blockface.geometry.coordinates.map(
        ([lng, lat]) => [lat, lng]
      );

      const polyline = L.polyline(latlngs, {
        color,
        weight: 8,
        opacity: 0.9,
      });

      // Add tooltip with status indicator
      let statusEmoji = '';
      if (color === '#eab308') {
        statusEmoji = '⚠️ '; // Yellow = mixed
      } else if (result.status === 'legal') {
        statusEmoji = '✅ ';
      } else if (result.status === 'illegal') {
        statusEmoji = '🚫 ';
      } else {
        statusEmoji = '🤔 ';
      }

      polyline.bindTooltip(statusEmoji + blockface.streetName, {
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