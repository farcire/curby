import { useState, useRef, useEffect } from 'react';
import { Logo } from '@/components/Logo';
import { SimpleDurationPicker } from '@/components/SimpleDurationPicker';
import { ParkingNavigator } from '@/components/ParkingNavigator';
import { MapView } from '@/components/MapView';
import { BlockfaceDetail } from '@/components/BlockfaceDetail';
import { ErrorReportDialog } from '@/components/ErrorReportDialog';
import { Blockface, LegalityResult } from '@/types/parking';
import { Sparkles, Map as MapIcon, Navigation } from 'lucide-react';
import { fetchSFMTABlockfaces } from '@/utils/sfmtaDataFetcher';
import { Button } from '@/components/ui/button';
import { showError } from '@/utils/toast';
import L from 'leaflet';

const DEFAULT_CENTER: [number, number] = [37.76272, -122.40920]; // 20th & Bryant - default fallback

const Index = () => {
  const [durationMinutes, setDurationMinutes] = useState(180); // Default to 3 hours
  const [selectedTime, setSelectedTime] = useState(new Date());
  const [selectedBlockface, setSelectedBlockface] = useState<Blockface | null>(null);
  const [legalityResult, setLegalityResult] = useState<LegalityResult | null>(null);
  const [showErrorDialog, setShowErrorDialog] = useState(false);
  const [blockfaces, setBlockfaces] = useState<Blockface[]>([]);
  const [isLoadingData, setIsLoadingData] = useState(true);
  const [viewMode, setViewMode] = useState<'navigator' | 'map'>('map');
  const [userLocation, setUserLocation] = useState<[number, number]>(DEFAULT_CENTER);
  const [hasInitialized, setHasInitialized] = useState(false);
  
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Get user's actual device location on startup
  useEffect(() => {
    if ('geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const userLoc: [number, number] = [
            position.coords.latitude,
            position.coords.longitude,
          ];
          setUserLocation(userLoc);
          // Load initial data centered on user location
          if (!hasInitialized) {
            loadSFMTAData(userLoc[0], userLoc[1], 300); // ~2 block radius
            setHasInitialized(true);
          }
        },
        (error) => {
          console.warn('Geolocation error:', error);
          // Fallback to default location
          setUserLocation(DEFAULT_CENTER);
          if (!hasInitialized) {
            loadSFMTAData(DEFAULT_CENTER[0], DEFAULT_CENTER[1], 300);
            setHasInitialized(true);
          }
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
  }, []);

  const loadSFMTAData = async (lat: number, lng: number, radius: number) => {
    setIsLoadingData(true);
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
      setIsLoadingData(false);
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

  const handleReportError = () => {
    setShowErrorDialog(true);
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


  return (
    <div className="h-screen w-screen flex flex-col bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 overflow-hidden">
      {/* Header */}
      <header className="bg-gradient-to-r from-purple-600 via-pink-600 to-orange-500 text-white p-2 shadow-md flex-shrink-0 relative overflow-hidden z-20">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-0 left-0 w-32 h-32 bg-white rounded-full -translate-x-16 -translate-y-16"></div>
          <div className="absolute bottom-0 right-0 w-40 h-40 bg-white rounded-full translate-x-20 translate-y-20"></div>
        </div>
        <div className="relative flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Logo size="sm" />
            <div>
              <h1 className="text-lg font-bold flex items-center gap-1.5 leading-none">
                Curby
                <Sparkles className="h-3 w-3 animate-pulse" />
              </h1>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setViewMode(viewMode === 'navigator' ? 'map' : 'navigator')}
              className="text-white hover:bg-white/20 rounded-full"
            >
              {viewMode === 'navigator' ? (
                <>
                  <MapIcon className="h-4 w-4 mr-1" />
                  Map
                </>
              ) : (
                <>
                  <Navigation className="h-4 w-4 mr-1" />
                  Navigate
                </>
              )}
            </Button>
          </div>
        </div>
      </header>

      {/* Loading */}
      {isLoadingData && (
        <div className="absolute inset-0 bg-gradient-to-br from-blue-50/95 via-purple-50/95 to-pink-50/95 backdrop-blur-sm z-50 flex items-center justify-center pointer-events-none">
          <div className="flex flex-col items-center justify-center text-center">
            <div className="mb-4">
              <Logo size="lg" animated={true} />
            </div>
            <p className="text-lg font-semibold text-gray-900 mb-1">Street parking eligibility made easy...</p>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="flex-1 relative overflow-hidden">
        {viewMode === 'navigator' ? (
          <ParkingNavigator
            blockfaces={blockfaces}
            durationMinutes={durationMinutes}
            onShowMap={() => setViewMode('map')}
          />
        ) : (
          <MapView
            checkTime={selectedTime}
            durationMinutes={durationMinutes}
            onBlockfaceClick={handleBlockfaceClick}
            blockfaces={blockfaces}
            initialCenter={userLocation}
            userLocation={userLocation}
            onMapMove={handleMapMove}
          />
        )}
      </div>

      {/* Floating Duration Picker - Replaces RadiusControl position */}
      {viewMode === 'map' && !selectedBlockface && (
        <SimpleDurationPicker
          durationMinutes={durationMinutes}
          onDurationChange={setDurationMinutes}
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
    </div>
  );
};

export default Index;