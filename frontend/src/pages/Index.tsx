import { useState, useRef, useEffect } from 'react';
import { Logo } from '@/components/Logo';
import { SimpleDurationPicker } from '@/components/SimpleDurationPicker';
import { MapView } from '@/components/MapView';
import { BlockfaceDetail } from '@/components/BlockfaceDetail';
import { ErrorReportDialog } from '@/components/ErrorReportDialog';
import { OutOfBoundsModal } from '@/components/OutOfBoundsModal';
import { EmbeddedSearch } from '@/components/EmbeddedSearch';
import { Blockface, LegalityResult } from '@/types/parking';
import { Sparkles } from 'lucide-react';
import { fetchSFMTABlockfaces } from '@/utils/sfmtaDataFetcher';
import { showError } from '@/utils/toast';
import { isInSanFrancisco, getDistanceToSF, SF_CENTER } from '@/utils/geoFence';
import L from 'leaflet';

const DEFAULT_CENTER: [number, number] = [37.76272, -122.40920]; // 20th & Bryant - default fallback

interface ParkingFilters {
  metered: boolean;
  nonMetered: boolean;
}

const Index = () => {
  const [durationMinutes, setDurationMinutes] = useState(180); // Default to 3 hours
  const [selectedTime, setSelectedTime] = useState(new Date());
  const [selectedBlockface, setSelectedBlockface] = useState<Blockface | null>(null);
  const [legalityResult, setLegalityResult] = useState<LegalityResult | null>(null);
  const [showErrorDialog, setShowErrorDialog] = useState(false);
  const [blockfaces, setBlockfaces] = useState<Blockface[]>([]);
  const [isInitialLoad, setIsInitialLoad] = useState(true);
  const [isFetching, setIsFetching] = useState(false);
  const [userLocation, setUserLocation] = useState<[number, number]>(DEFAULT_CENTER);
  const [hasInitialized, setHasInitialized] = useState(false);
  const [showOutOfBoundsModal, setShowOutOfBoundsModal] = useState(false);
  const [distanceToSF, setDistanceToSF] = useState<number>(0);
  const [searchedLocation, setSearchedLocation] = useState<[number, number] | null>(null);
  const [searchedLocationName, setSearchedLocationName] = useState<string>('');
  const [showFreeOnly, setShowFreeOnly] = useState(false);
  
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Get user's actual device location on startup
  useEffect(() => {
    let watchId: number | null = null;

    if ('geolocation' in navigator) {
      // Use watchPosition to keep track of user location for the blue dot
      watchId = navigator.geolocation.watchPosition(
        (position) => {
          const userLoc: [number, number] = [
            position.coords.latitude,
            position.coords.longitude,
          ];
          setUserLocation(userLoc);
          
          // Only load initial data once when we get the first fix
          if (!hasInitialized) {
            // Check if user is in San Francisco
            if (!isInSanFrancisco(userLoc[0], userLoc[1])) {
              const distance = getDistanceToSF(userLoc[0], userLoc[1]);
              setDistanceToSF(distance);
              setShowOutOfBoundsModal(true);
              // Load SF map in background
              loadSFMTAData(SF_CENTER[0], SF_CENTER[1], 500);
            } else {
              loadSFMTAData(userLoc[0], userLoc[1], 300); // ~2 block radius
            }
            setHasInitialized(true);
          }
        },
        (error) => {
          console.warn('Geolocation error:', error);
          // Fallback to default location if we haven't initialized yet
          if (!hasInitialized) {
            setUserLocation(DEFAULT_CENTER);
            loadSFMTAData(DEFAULT_CENTER[0], DEFAULT_CENTER[1], 300);
            setHasInitialized(true);
          }
        },
        {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 0,
        }
      );
    } else {
      // Geolocation not supported, use default
      setUserLocation(DEFAULT_CENTER);
      if (!hasInitialized) {
        loadSFMTAData(DEFAULT_CENTER[0], DEFAULT_CENTER[1], 300);
        setHasInitialized(true);
      }
    }

    return () => {
      if (watchId !== null) {
        navigator.geolocation.clearWatch(watchId);
      }
    };
  }, [hasInitialized]);

  const loadSFMTAData = async (lat: number, lng: number, radius: number) => {
    setIsFetching(true);
    try {
      const sfmtaData = await fetchSFMTABlockfaces(lat, lng, radius);
      setBlockfaces(sfmtaData);
      
      if (sfmtaData.length === 0) {
        console.log('No data found in this area');
      }
    } catch (error) {
      console.error('Error loading SFMTA data:', error);
      setBlockfaces([]);
      showError('Failed to load parking data');
    } finally {
      setIsFetching(false);
      setIsInitialLoad(false);
    }
  };

  const handleMapMove = (bounds: L.LatLngBounds) => {
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    debounceTimerRef.current = setTimeout(() => {
      const center = bounds.getCenter();
      const northEast = bounds.getNorthEast();
      // Calculate radius from center to corner to cover the view
      const radiusMeters = center.distanceTo(northEast);
      
      loadSFMTAData(center.lat, center.lng, radiusMeters);
    }, 500);
  };

  const handleBlockfaceClick = (blockface: Blockface, result: LegalityResult) => {
    setSelectedBlockface(blockface);
    setLegalityResult(result);
  };

  const handleCloseDetail = () => {
    setSelectedBlockface(null);
    setLegalityResult(null);
  };

  const handleMapClick = () => {
    // Close blockface detail when clicking empty map area
    if (selectedBlockface) {
      handleCloseDetail();
    }
  };

  const handleReportError = () => {
    setShowErrorDialog(true);
  };

  const handleLocationSelect = (coords: [number, number], name: string) => {
    setSearchedLocation(coords);
    setSearchedLocationName(name);
    loadSFMTAData(coords[0], coords[1], 300);
  };

  // Calculate distance between two points
  const calculateDistance = (lat1: number, lng1: number, lat2: number, lng2: number): number => {
    const R = 6371e3;
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

  // Filter blockfaces based on free parking toggle
  const filteredBlockfaces = showFreeOnly
    ? blockfaces.filter(blockface => {
        // Show only spots without meters
        const hasMeters = blockface.rules.some(rule => rule.type === 'meter');
        return !hasMeters;
      })
    : blockfaces;

  return (
    <div className="h-screen w-screen flex flex-col bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 overflow-hidden">
      {/* Header */}
      <header className="bg-gradient-to-r from-purple-600 via-pink-600 to-orange-500 text-white p-4 shadow-md flex-shrink-0 relative overflow-visible z-[100]">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-0 left-0 w-32 h-32 bg-white rounded-full -translate-x-16 -translate-y-16"></div>
          <div className="absolute bottom-0 right-0 w-40 h-40 bg-white rounded-full translate-x-20 translate-y-20"></div>
        </div>
        <div className="relative flex items-center justify-between gap-6">
          <div className="flex items-center gap-2 flex-shrink-0">
            <Logo size="sm" />
            <div>
              <h1 className="text-lg font-bold flex items-center gap-1.5 leading-none">
                Curby
                <Sparkles className="h-3 w-3 animate-pulse" />
              </h1>
            </div>
          </div>
          <div className="flex-1 max-w-md ml-auto">
            <EmbeddedSearch onLocationSelect={handleLocationSelect} />
          </div>
        </div>
      </header>

      {/* Initial Loading Screen */}
      {isInitialLoad && (
        <div className="absolute inset-0 bg-gradient-to-br from-blue-50/95 via-purple-50/95 to-pink-50/95 backdrop-blur-sm z-50 flex items-center justify-center pointer-events-none transition-opacity duration-500">
          <div className="flex flex-col items-center justify-center text-center">
            <div className="mb-4">
              <Logo size="lg" animated={true} />
            </div>
            <p className="text-lg font-semibold text-gray-900 mb-1">Street parking eligibility made easy...</p>
          </div>
        </div>
      )}

      {/* Subtle Background Loading Indicator */}
      {isFetching && !isInitialLoad && (
        <div className="absolute top-[72px] left-1/2 transform -translate-x-1/2 z-40 bg-white/90 backdrop-blur-sm px-3 py-1.5 rounded-full shadow-sm border border-purple-100 flex items-center gap-2">
          <Sparkles className="h-3.5 w-3.5 text-purple-600 animate-spin" />
          <span className="text-xs font-medium text-purple-900">Updating map...</span>
        </div>
      )}

      {/* Main Content */}
      <div className="flex-1 relative overflow-hidden">
        <MapView
          checkTime={selectedTime}
          durationMinutes={durationMinutes}
          onBlockfaceClick={handleBlockfaceClick}
          blockfaces={filteredBlockfaces}
          initialCenter={userLocation}
          userLocation={userLocation}
          onMapMove={handleMapMove}
          searchedLocation={searchedLocation}
          searchedLocationName={searchedLocationName}
          onMapClick={handleMapClick}
        />
      </div>

      {/* Floating Duration Picker */}
      {!selectedBlockface && (
        <SimpleDurationPicker
          durationMinutes={durationMinutes}
          onDurationChange={setDurationMinutes}
          showFreeOnly={showFreeOnly}
          onToggleFreeOnly={() => setShowFreeOnly(!showFreeOnly)}
        />
      )}

      {/* Blockface Detail Panel */}
      {selectedBlockface && legalityResult && (
        <BlockfaceDetail
          blockface={selectedBlockface}
          legalityResult={legalityResult}
          onReportError={handleReportError}
          onClose={handleCloseDetail}
        />
      )}

      {/* Error Report Dialog */}
      <ErrorReportDialog
        open={showErrorDialog}
        onOpenChange={setShowErrorDialog}
        blockface={selectedBlockface}
      />

      {/* Out of Bounds Modal */}
      {showOutOfBoundsModal && (
        <OutOfBoundsModal
          distanceKm={distanceToSF}
          onViewSF={() => setShowOutOfBoundsModal(false)}
          onSearchAddress={() => {
            setShowOutOfBoundsModal(false);
            // Search is now always visible in header
          }}
          onDismiss={() => setShowOutOfBoundsModal(false)}
        />
      )}
    </div>
  );
};

export default Index;