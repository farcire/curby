import { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { Blockface, LegalityResult } from '@/types/parking';
import { evaluateLegality, getStatusColor } from '@/utils/ruleEngine';
import { renderToString } from 'react-dom/server';
import { Logo } from './Logo';

interface MapViewProps {
  checkTime: Date;
  durationMinutes: number;
  onBlockfaceClick: (blockface: Blockface, result: LegalityResult) => void;
  blockfaces: Blockface[];
  initialCenter: [number, number]; // [lat, lng] - initial map center
  userLocation?: [number, number]; // [lat, lng] - user's actual device location
  onMapMove?: (bounds: L.LatLngBounds) => void;
  onNavigateToUser?: () => void;
}

interface BlockfaceWithResult {
  blockface: Blockface;
  result: LegalityResult;
}

export function MapView({
  checkTime,
  durationMinutes,
  onBlockfaceClick,
  blockfaces,
  initialCenter,
  userLocation,
  onMapMove,
  onNavigateToUser,
}: MapViewProps) {
  const mapRef = useRef<L.Map | null>(null);
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const layersRef = useRef<L.Polyline[]>([]);
  const userMarkerRef = useRef<L.Marker | null>(null);
  const userHasInteractedRef = useRef(false);

  // Initialize map (only once)
  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return;

    // Initial zoom 18 (Immediate Detail)
    const initialZoom = 18;

    const map = L.map(mapContainerRef.current, {
      center: initialCenter,
      zoom: initialZoom,
      zoomControl: false,
      minZoom: 13, // City-wide Context
      maxZoom: 18, // Immediate Vicinity
      maxBounds: null, // Explicitly allow unrestricted panning
      maxBoundsViscosity: 0,
    });

    // Add zoom control at top-left position
    L.control.zoom({ position: 'topleft' }).addTo(map);

    // Notify parent of initial bounds
    if (onMapMove) {
      onMapMove(map.getBounds());
    }

    map.on('moveend', () => {
      if (onMapMove) {
        onMapMove(map.getBounds());
      }
    });

    // Track user interaction to prevent unwanted auto-centering
    map.on('dragstart', () => {
      userHasInteractedRef.current = true;
    });
    map.on('zoomstart', () => {
      userHasInteractedRef.current = true;
    });

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    }).addTo(map);

    mapRef.current = map;

    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, []); // Only initialize once

  const hasCenteredRef = useRef(false);
  const DEFAULT_LAT = 37.76272;

  // Center map on user location only once when a real location is found
  useEffect(() => {
    if (mapRef.current && userLocation) {
        // Check if this is likely the default location
        const isDefault = Math.abs(userLocation[0] - DEFAULT_LAT) < 0.00001;

        // Only center if:
        // 1. It's a real location (not default)
        // 2. We haven't centered yet
        // 3. The user hasn't already started manually interacting with the map
        if (!isDefault && !hasCenteredRef.current && !userHasInteractedRef.current) {
            mapRef.current.setView(userLocation, 18, { animate: true });
            hasCenteredRef.current = true;
        }
    }
  }, [userLocation]);

  // Update user location marker (stays at user's actual location)
  useEffect(() => {
    if (!mapRef.current || !userLocation) return;

    // Remove existing marker if any
    if (userMarkerRef.current) {
      mapRef.current.removeLayer(userMarkerRef.current);
    }

    // Create Curby logo marker using the actual logo design
    const logoHtml = renderToString(<Logo size="sm" />);
    const userMarker = L.marker(userLocation, {
      icon: L.divIcon({
        className: 'custom-user-marker',
        html: `
          <div style="
            width: 32px;
            height: 32px;
            filter: drop-shadow(0 2px 8px rgba(139, 92, 246, 0.4));
          ">
            ${logoHtml}
          </div>
        `,
        iconSize: [32, 32],
        iconAnchor: [16, 16],
      }),
      zIndexOffset: 1000, // Keep marker on top
    }).addTo(mapRef.current);

    userMarker.bindTooltip('📍 Your Location', {
      permanent: false,
      direction: 'top',
      offset: [0, -20],
    });

    userMarkerRef.current = userMarker;
  }, [userLocation]);

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
      // Debug logging for address ranges
      if (blockface.streetName.includes('YORK')) {
        console.log('York St Blockface:', {
          id: blockface.id,
          from: blockface.fromAddress,
          to: blockface.toAddress,
          side: blockface.side,
          cardinal: blockface.cardinalDirection
        });
      }

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

      // Format label: "Street Name (Side/Cardinal, Start-End)"
      const sideText = blockface.cardinalDirection || blockface.side;
      let label = `${statusEmoji} ${blockface.streetName} (${sideText}`;
      if (blockface.fromAddress && blockface.toAddress) {
        label += `, ${blockface.fromAddress}-${blockface.toAddress}`;
      }
      label += ')';

      polyline.bindTooltip(
        label,
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

  // Handle navigate to user location
  const handleNavigateToUser = () => {
    if (mapRef.current && userLocation) {
      mapRef.current.setView(userLocation, 18, { animate: true });
    }
    if (onNavigateToUser) {
      onNavigateToUser();
    }
  };

  return (
    <>
      <div
        ref={mapContainerRef}
        className="absolute inset-0 w-full h-full"
        style={{ zIndex: 0 }}
      />
      
      {/* Navigate to User Location Button - styled to match Leaflet controls */}
      {userLocation && (
        <button
          onClick={handleNavigateToUser}
          className="leaflet-control leaflet-bar absolute top-[94px] left-[10px] z-[1000] bg-white hover:bg-gray-50 text-gray-900 rounded-sm shadow-md border border-gray-300/50 transition-colors w-[30px] h-[30px] flex items-center justify-center"
          title="Return to your location"
          style={{
            cursor: 'pointer',
            fontSize: '18px',
            lineHeight: '30px',
            textAlign: 'center'
          }}
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="text-gray-700"
          >
            <circle cx="12" cy="12" r="3" />
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="2" x2="12" y2="4" />
            <line x1="12" y1="20" x2="12" y2="22" />
            <line x1="2" y1="12" x2="4" y2="12" />
            <line x1="20" y1="12" x2="22" y2="12" />
          </svg>
        </button>
      )}
    </>
  );
}