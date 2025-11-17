import { useState, useEffect } from 'react';
import { Logo } from '@/components/Logo';
import { SimpleDurationPicker } from '@/components/SimpleDurationPicker';
import { ParkingNavigator } from '@/components/ParkingNavigator';
import { MapView } from '@/components/MapView';
import { BlockfaceDetail } from '@/components/BlockfaceDetail';
import { ErrorReportDialog } from '@/components/ErrorReportDialog';
import { Blockface, LegalityResult } from '@/types/parking';
import { Sparkles, RefreshCw, Map as MapIcon, Navigation } from 'lucide-react';
import { fetchSFMTABlockfaces, clearSFMTACache } from '@/utils/sfmtaDataFetcher';
import { mockBlockfaces } from '@/data/mockBlockfaces';
import { Button } from '@/components/ui/button';
import { showSuccess, showError } from '@/utils/toast';

const Index = () => {
  const [durationMinutes, setDurationMinutes] = useState(60);
  const [selectedBlockface, setSelectedBlockface] = useState<Blockface | null>(null);
  const [legalityResult, setLegalityResult] = useState<LegalityResult | null>(null);
  const [showErrorDialog, setShowErrorDialog] = useState(false);
  const [blockfaces, setBlockfaces] = useState<Blockface[]>(mockBlockfaces);
  const [isLoadingData, setIsLoadingData] = useState(true);
  const [dataSource, setDataSource] = useState<'mock' | 'sfmta'>('mock');
  const [viewMode, setViewMode] = useState<'navigator' | 'map'>('navigator');

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
        showSuccess(`🎉 Found ${sfmtaData.length} parking spots!`);
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

  return (
    <div className="h-screen w-screen flex flex-col bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 overflow-hidden">
      {/* Whimsical Header with Logo */}
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
              <p className="text-sm text-white/90">street parking eligibility made easy.</p>
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

      {/* Simple Duration Picker */}
      <div className="flex-shrink-0">
        <SimpleDurationPicker
          durationMinutes={durationMinutes}
          onDurationChange={setDurationMinutes}
        />
      </div>

      {/* Playful Data Source Banner */}
      {dataSource === 'mock' && (
        <div className="bg-gradient-to-r from-amber-50 to-orange-50 border-b border-amber-200 px-4 py-2 flex-shrink-0">
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2 text-xs text-amber-900">
              <span className="text-lg">🎪</span>
              <span>Demo mode - showing sample data</span>
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

      {/* Loading with Personality */}
      {isLoadingData && (
        <div className="absolute inset-0 bg-gradient-to-br from-blue-50/95 via-purple-50/95 to-pink-50/95 backdrop-blur-sm z-50 flex items-center justify-center">
          <div className="text-center">
            <div className="relative mb-4">
              <Logo size="lg" />
              <div className="absolute inset-0 animate-ping opacity-20">
                <Logo size="lg" />
              </div>
            </div>
            <p className="text-lg font-semibold text-gray-900 mb-2">Finding spots...</p>
            <p className="text-sm text-gray-600">✨ Just a sec ✨</p>
          </div>
        </div>
      )}

      {/* Main Content - Navigator or Map */}
      {viewMode === 'navigator' ? (
        <ParkingNavigator
          blockfaces={blockfaces}
          durationMinutes={durationMinutes}
          onShowMap={() => setViewMode('map')}
        />
      ) : (
        <div className="flex-1 relative min-h-0">
          <MapView
            checkTime={new Date()}
            durationMinutes={durationMinutes}
            onBlockfaceClick={handleBlockfaceClick}
            blockfaces={blockfaces}
          />
        </div>
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