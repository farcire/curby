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

const CENTER_POINT: [number, number] = [37.75872, -122.40920]; // Real 20th & Bryant intersection

const Index = () => {
  const [durationMinutes, setDurationMinutes] = useState(60);
  const [radiusBlocks, setRadiusBlocks] = useState(3);
  const [selectedTime, setSelectedTime] = useState(new Date());
  const [selectedBlockface, setSelectedBlockface] = useState<Blockface | null>(null);
  const [legalityResult, setLegalityResult] = useState<LegalityResult | null>(null);
  const [showErrorDialog, setShowErrorDialog] = useState(false);
  const [blockfaces, setBlockfaces] = useState<Blockface[]>(mockBlockfaces);
  const [isLoadingData, setIsLoadingData] = useState(true);
  const [dataSource, setDataSource] = useState<'mock' | 'sfmta'>('mock');
  const [viewMode, setViewMode] = useState<'navigator' | 'map'>('map');

  useEffect(() => {
    loadSFMTAData();
  }, []);

  const loadSFMTAData = async () => {
    setIsLoadingData(true);
    try {
      const sfmtaData = await fetchSFMTABlockfaces();
      
      if (sfmtaData.length > 0) {
        setBlockfaces(sfmtaData);
        setDataSource('sfmta');
        showSuccess(`Found ${sfmtaData.length} parking spots!`);
      } else {
        setBlockfaces(mockBlockfaces);
        setDataSource('mock');
        showError('Using demo data - real data coming soon!');
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
      <header className="bg-gradient-to-r from-purple-600 via-pink-600 to-orange-500 text-white p-4 shadow-lg flex-shrink-0 relative overflow-hidden">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-0 left-0 w-32 h-32 bg-white rounded-full -translate-x-16 -translate-y-16"></div>
          <div className="absolute bottom-0 right-0 w-40 h-40 bg-white rounded-full translate-x-20 translate-y-20"></div>
        </div>
        <div className="relative flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Logo size="md" />
            <div>
              <h1 className="text-2xl font-bold flex items-center gap-2">
                Curby
                <Sparkles className="h-5 w-5 animate-pulse" />
              </h1>
              <p className="text-sm text-white/90">street parking eligibility made easy</p>
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

      {/* Data Source Banner */}
      {dataSource === 'mock' && (
        <div className="bg-gradient-to-r from-amber-50 to-orange-50 border-b border-amber-200 px-4 py-2 flex-shrink-0">
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2 text-xs text-amber-900">
              <Logo size="sm" />
              <span>Demo mode - 3 blocks around 20th & Bryant</span>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleRefreshData}
              className="text-amber-900 hover:text-amber-950 hover:bg-amber-100 rounded-full h-7 text-xs"
            >
              <RefreshCw className="h-3 w-3 mr-1" />
              Retry
            </Button>
          </div>
        </div>
      )}

      {/* Loading */}
      {isLoadingData && (
        <div className="absolute inset-0 bg-gradient-to-br from-blue-50/95 via-purple-50/95 to-pink-50/95 backdrop-blur-sm z-50 flex items-center justify-center">
          <div className="text-center">
            <div className="relative mb-4">
              <Logo size="lg" animated={true} />
            </div>
            <p className="text-lg font-semibold text-gray-900 mb-2">Finding spots...</p>
            <p className="text-sm text-gray-600">✨ Just a sec ✨</p>
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