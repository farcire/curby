import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Navigation, ArrowLeft, ArrowRight, ArrowUp, MapPin, Loader2 } from 'lucide-react';
import { Blockface } from '@/types/parking';
import { evaluateLegality } from '@/utils/ruleEngine';

interface ParkingNavigatorProps {
  blockfaces: Blockface[];
  durationMinutes: number;
  onShowMap: () => void;
}

interface LocationState {
  lat: number;
  lng: number;
  heading: number | null;
}

interface ParkingDirection {
  direction: 'ahead' | 'left' | 'right';
  distance: number; // meters
  streetName: string;
  status: 'legal' | 'illegal' | 'insufficient-data';
  blockface: Blockface;
}

export function ParkingNavigator({ blockfaces, durationMinutes, onShowMap }: ParkingNavigatorProps) {
  const [location, setLocation] = useState<LocationState | null>(null);
  const [locationError, setLocationError] = useState<string | null>(null);
  const [isLoadingLocation, setIsLoadingLocation] = useState(true);
  const [nearbyParking, setNearbyParking] = useState<ParkingDirection[]>([]);

  // Get user's actual device location
  useEffect(() => {
    if ('geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setLocation({
            lat: position.coords.latitude,
            lng: position.coords.longitude,
            heading: position.coords.heading, // May be null if not available
          });
          setIsLoadingLocation(false);
        },
        (error) => {
          console.error('Geolocation error:', error);
          setLocationError('Unable to access your location. Please enable location services.');
          setIsLoadingLocation(false);
        },
        {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 0,
        }
      );
    } else {
      setLocationError('Geolocation is not supported by your browser.');
      setIsLoadingLocation(false);
    }
  }, []);

  // Get device orientation for heading if not provided by GPS
  useEffect(() => {
    if (location?.heading !== null) return;

    const handleOrientation = (event: DeviceOrientationEvent) => {
      if (event.alpha !== null && location) {
        setLocation({
          ...location,
          heading: 360 - event.alpha, // Convert to compass heading
        });
      }
    };

    window.addEventListener('deviceorientation', handleOrientation);
    return () => window.removeEventListener('deviceorientation', handleOrientation);
  }, [location]);

  // Calculate nearby parking based on location and heading
  useEffect(() => {
    if (!location || !location.heading) return;

    const nearby: ParkingDirection[] = [];
    const checkTime = new Date();

    blockfaces.forEach((blockface) => {
      // Get blockface center point
      const coords = blockface.geometry.coordinates;
      const centerLat = coords.reduce((sum, c) => sum + c[1], 0) / coords.length;
      const centerLng = coords.reduce((sum, c) => sum + c[0], 0) / coords.length;

      // Calculate distance
      const distance = calculateDistance(
        location.lat,
        location.lng,
        centerLat,
        centerLng
      );

      // Only consider blockfaces within 200 meters
      if (distance > 200) return;

      // Calculate bearing from user to blockface
      const bearing = calculateBearing(
        location.lat,
        location.lng,
        centerLat,
        centerLng
      );

      // Determine direction relative to user's heading
      const relativeBearing = (bearing - location.heading! + 360) % 360;
      let direction: 'ahead' | 'left' | 'right';

      if (relativeBearing < 45 || relativeBearing > 315) {
        direction = 'ahead';
      } else if (relativeBearing >= 45 && relativeBearing < 180) {
        direction = 'right';
      } else {
        direction = 'left';
      }

      // Evaluate parking legality
      const result = evaluateLegality(blockface, checkTime, durationMinutes);

      nearby.push({
        direction,
        distance,
        streetName: blockface.streetName,
        status: result.status,
        blockface,
      });
    });

    // Sort by distance and take closest options
    nearby.sort((a, b) => a.distance - b.distance);
    setNearbyParking(nearby.slice(0, 6));
  }, [location, blockfaces, durationMinutes]);

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

  // Calculate bearing between two points
  const calculateBearing = (lat1: number, lng1: number, lat2: number, lng2: number): number => {
    const φ1 = (lat1 * Math.PI) / 180;
    const φ2 = (lat2 * Math.PI) / 180;
    const Δλ = ((lng2 - lng1) * Math.PI) / 180;

    const y = Math.sin(Δλ) * Math.cos(φ2);
    const x = Math.cos(φ1) * Math.sin(φ2) - Math.sin(φ1) * Math.cos(φ2) * Math.cos(Δλ);
    const θ = Math.atan2(y, x);

    return ((θ * 180) / Math.PI + 360) % 360;
  };

  const formatDistance = (meters: number): string => {
    if (meters < 100) return `${Math.round(meters)}m`;
    return `${(meters / 1000).toFixed(1)}km`;
  };

  const getDirectionIcon = (direction: 'ahead' | 'left' | 'right') => {
    switch (direction) {
      case 'ahead':
        return <ArrowUp className="h-6 w-6" />;
      case 'left':
        return <ArrowLeft className="h-6 w-6" />;
      case 'right':
        return <ArrowRight className="h-6 w-6" />;
    }
  };

  const getStatusColor = (status: 'legal' | 'illegal' | 'insufficient-data') => {
    switch (status) {
      case 'legal':
        return 'bg-green-500';
      case 'illegal':
        return 'bg-red-500';
      case 'insufficient-data':
        return 'bg-gray-400';
    }
  };

  const getStatusEmoji = (status: 'legal' | 'illegal' | 'insufficient-data') => {
    switch (status) {
      case 'legal':
        return '✅';
      case 'illegal':
        return '🚫';
      case 'insufficient-data':
        return '🤔';
    }
  };

  // Find best parking option
  const bestOption = nearbyParking.find((p) => p.status === 'legal');

  if (isLoadingLocation) {
    return (
      <div className="flex-1 flex items-center justify-center bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50">
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin text-purple-600 mx-auto mb-4" />
          <p className="text-lg font-semibold text-gray-900 mb-2">Locating & Decoding Regulations...</p>
          <p className="text-sm text-gray-600">📍 Analyzing street rules nearby</p>
        </div>
      </div>
    );
  }

  if (locationError) {
    return (
      <div className="flex-1 flex items-center justify-center bg-gradient-to-br from-orange-50 to-red-50 p-6">
        <Card className="p-6 max-w-md">
          <div className="text-center">
            <MapPin className="h-12 w-12 text-red-500 mx-auto mb-4" />
            <h3 className="text-lg font-bold text-gray-900 mb-2">Location Needed</h3>
            <p className="text-sm text-gray-600 mb-4">
              We need your location to show you nearby parking. Please enable location access in your browser settings.
            </p>
            <Button onClick={onShowMap} className="rounded-xl">
              View Map Instead
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  if (!location?.heading) {
    return (
      <div className="flex-1 flex items-center justify-center bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 p-6">
        <Card className="p-6 max-w-md">
          <div className="text-center">
            <Navigation className="h-12 w-12 text-purple-600 mx-auto mb-4 animate-pulse" />
            <h3 className="text-lg font-bold text-gray-900 mb-2">Getting your direction...</h3>
            <p className="text-sm text-gray-600 mb-4">
              Move your device around to calibrate the compass
            </p>
            <Button onClick={onShowMap} variant="outline" className="rounded-xl">
              View Map Instead
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 overflow-y-auto">
      {/* Best Option Banner */}
      {bestOption && (
        <div className="bg-gradient-to-r from-green-500 to-emerald-600 text-white p-6 shadow-lg">
          <div className="flex items-center gap-4">
            <div className="bg-white/20 backdrop-blur-sm rounded-2xl p-3">
              {getDirectionIcon(bestOption.direction)}
            </div>
            <div className="flex-1">
              <p className="text-sm font-semibold uppercase tracking-wide opacity-90">
                {bestOption.direction === 'ahead' ? 'Keep Going' : `Turn ${bestOption.direction}`}
              </p>
              <p className="text-2xl font-bold">{bestOption.streetName}</p>
              <p className="text-sm opacity-90">{formatDistance(bestOption.distance)} away</p>
            </div>
            <div className="text-4xl">🎉</div>
          </div>
        </div>
      )}

      {/* No Parking Available */}
      {!bestOption && nearbyParking.length > 0 && (
        <div className="bg-gradient-to-r from-amber-500 to-orange-600 text-white p-6 shadow-lg">
          <div className="flex items-center gap-4">
            <div className="text-4xl">🔍</div>
            <div className="flex-1">
              <p className="text-2xl font-bold">Keep looking...</p>
              <p className="text-sm opacity-90">No legal parking nearby right now</p>
            </div>
          </div>
        </div>
      )}

      {/* Nearby Options */}
      <div className="p-4 space-y-3">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-bold text-gray-900 flex items-center gap-2">
            <MapPin className="h-4 w-4" />
            Nearby Parking
          </h3>
          <Button variant="ghost" size="sm" onClick={onShowMap} className="text-xs rounded-full">
            View Map
          </Button>
        </div>

        {nearbyParking.length === 0 && (
          <Card className="p-6 text-center">
            <div className="text-4xl mb-3">🗺️</div>
            <p className="text-sm text-gray-600">No parking data nearby</p>
            <Button onClick={onShowMap} className="mt-4 rounded-xl">
              View Full Map
            </Button>
          </Card>
        )}

        {nearbyParking.map((parking, idx) => (
          <Card
            key={idx}
            className={`p-4 border-2 ${
              parking.status === 'legal'
                ? 'border-green-300 bg-green-50'
                : parking.status === 'illegal'
                ? 'border-red-300 bg-red-50'
                : 'border-gray-300 bg-gray-50'
            }`}
          >
            <div className="flex items-center gap-3">
              <div
                className={`${getStatusColor(parking.status)} text-white rounded-xl p-2 flex-shrink-0`}
              >
                {getDirectionIcon(parking.direction)}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <p className="font-semibold text-gray-900 truncate">{parking.streetName}</p>
                  <span className="text-lg">{getStatusEmoji(parking.status)}</span>
                </div>
                <div className="flex items-center gap-3 text-xs text-gray-600">
                  <span className="font-medium">{formatDistance(parking.distance)}</span>
                  <span className="capitalize">{parking.direction}</span>
                </div>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}