import { useState, useEffect } from 'react';
import { Logo } from '@/components/Logo';
import { SimpleDurationPicker } from '@/components/SimpleDurationPicker';
import { ParkingNavigator } from '@/components/ParkingNavigator';
import { MapView } from '@/components/MapView';
import { BlockfaceDetail } from '@/components/BlockfaceDetail';
import { ErrorReportDialog } from '@/components/ErrorReportDialog';
import { RadiusControl } from '@/components/RadiusControl';
import { Blockface, LegalityResult } from '@/types/parking';
import { Sparkles, RefreshCw, Map as MapIcon, Navigation } from 'lucide-react';
import { fetchSFMTABlockfaces, clearSFMTACache } from '@/utils/sfmtaDataFetcher';
import { mockBlockfaces } from '@/data/mockBlockfaces';
import { Button } from '@/components/ui/button';
import { showSuccess, showError } from '@/utils/toast';
import { evaluateLegality } from '@/utils/ruleEngine';

const CENTER_POINT: [number, number] = [37.76272, -122.40920]; // 20th & Bryant - adjusted north

const Index = () => {
  const [durationMinutes, setDurationMinutes] = useState(60);
  // Default radius to 2 blocks as per refined PRD
  const [radiusBlocks, setRadiusBlocks] = useState(2);
  const [selectedTime, setSelectedTime] = useState(new Date());
  const [selectedBlockface, setSelectedBlockface] = useState<Blockface | null>(null);
  const [legalityResult, setLegalityResult] = useState<LegalityResult | null>(null);
  const [showErrorDialog, setShowErrorDialog] = useState(false);
  const [blockfaces, setBlockfaces] = useState<Blockface[]>(mockBlockfaces);
  const [isLoadingData, setIsLoadingData] = useState(true);
  const [dataSource, setDataSource] = useState<'mock' | 'sfmta'>('mock');
  const [viewMode, setViewMode] = useState<'navigator' | 'map'>('map');

  // Load data on mount and when radius changes
  useEffect(() => {
    const timer = setTimeout(() => {
      loadSFMTAData();
    }, 500); // Debounce for 500ms

    return () => clearTimeout(timer);
  }, [radiusBlocks]);

  const loadSFMTAData = async () => {
    setIsLoadingData(true);
    try {
      // Convert blocks to meters (approx 110m per block)
      const radiusMeters = radiusBlocks * 110;
      // Add a buffer to ensure coverage
      const fetchRadius = Math.max(radiusMeters * 1.5, 300);

      const sfmtaData = await fetchSFMTABlockfaces(CENTER_POINT[0], CENTER_POINT[1], fetchRadius);
      
      if (sfmtaData.length > 0) {
        setBlockfaces(sfmtaData);
        setDataSource('sfmta');
      } else {
        setBlockfaces(mockBlockfaces);
        setDataSource('mock');
        if (dataSource === 'sfmta') { // Only show error if we were previously connected
             showError('Using demo data - real data coming soon!');
        }
      }
    } catch (error) {
      console.error('Error loading SFMTA data:', error);
      setBlockfaces(mockBlockfaces);
      setDataSource('mock');
      showError('Using demo data - real data coming soon!');
    } finally {
      setIsLoadingData(false);
    }
  };

  const handleRefreshData = async () => {
    clearSFMTACache();
    await loadSFMTAData();
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

  // Calculate radius stats
  const radiusMeters = radiusBlocks * 110;
  
  const blockfacesWithDistance = blockfaces.map(blockface => {
    const [centerLat, centerLng] = getBlockfaceCenter(blockface);
    const distance = calculateDistance(CENTER_POINT[0], CENTER_POINT[1], centerLat, centerLng);
    const result = evaluateLegality(blockface, selectedTime, durationMinutes);
    
    return {
      blockface,
      distance,
      result,
    };
  });

  const blocksInRadius = blockfacesWithDistance.filter(b => b.distance <= radiusMeters);
  const legalBlocksInRadius = blocksInRadius.filter(b => b.result.status === 'legal').length;
  
  // Find nearest legal parking outside radius
  const blocksOutsideRadius = blockfacesWithDistance
    .filter(b => b.distance > radiusMeters && b.result.status === 'legal')
    .sort((a, b) => a.distance - b.distance);
  
  const nearestLegal = blocksOutsideRadius[0];

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

      {/* Duration Picker */}
      <div className="flex-shrink-0">
        <SimpleDurationPicker
          durationMinutes={durationMinutes}
          onDurationChange={setDurationMinutes}
        />
      </div>

      {/* Loading */}
      {isLoadingData && (
        <div className="absolute inset-0 bg-gradient-to-br from-blue-50/95 via-purple-50/95 to-pink-50/95 backdrop-blur-sm z-50 flex items-center justify-center">
          <div className="text-center">
            <div className="relative mb-4">
              <Logo size="lg" animated={true} />
            </div>
            <p className="text-lg font-semibold text-gray-900 mb-1">Street parking eligibility made easy...</p>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="flex-1 relative overflow-hidden pb-20">
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
            radiusBlocks={radiusBlocks}
            centerPoint={CENTER_POINT}
          />
        )}
      </div>

      {/* Radius Control - Only show when detail panel is NOT open */}
      {viewMode === 'map' && !selectedBlockface && (
        <RadiusControl
          radiusBlocks={radiusBlocks}
          onRadiusChange={setRadiusBlocks}
          legalBlocksInRadius={legalBlocksInRadius}
          totalBlocksInRadius={blocksInRadius.length}
          nearestLegalDistance={nearestLegal?.distance}
          nearestLegalStreet={nearestLegal?.blockface.streetName}
          selectedTime={selectedTime}
          durationMinutes={durationMinutes}
          onTimeChange={setSelectedTime}
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