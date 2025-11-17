import { useState, useEffect } from 'react';
import { TimeControls } from '@/components/TimeControls';
import { MapView } from '@/components/MapView';
import { BlockfaceDetail } from '@/components/BlockfaceDetail';
import { ErrorReportDialog } from '@/components/ErrorReportDialog';
import { Blockface, LegalityResult } from '@/types/parking';
import { Card } from '@/components/ui/card';
import { Info, AlertCircle, RefreshCw } from 'lucide-react';
import { fetchSFMTABlockfaces, clearSFMTACache } from '@/utils/sfmtaDataFetcher';
import { mockBlockfaces } from '@/data/mockBlockfaces';
import { Button } from '@/components/ui/button';
import { showSuccess, showError } from '@/utils/toast';

const Index = () => {
  // Demo scenario: Monday at 12:00 PM, need 60 minutes of parking
  const getDemoTime = () => {
    const now = new Date();
    // Set to Monday at noon
    const demo = new Date(now);
    demo.setHours(12, 0, 0, 0);
    // Find next Monday (or use today if it's Monday)
    const dayOfWeek = demo.getDay();
    const daysUntilMonday = dayOfWeek === 1 ? 0 : (8 - dayOfWeek) % 7;
    demo.setDate(demo.getDate() + daysUntilMonday);
    return demo;
  };

  const [selectedTime, setSelectedTime] = useState(getDemoTime());
  const [durationMinutes, setDurationMinutes] = useState(60); // 60 minutes for demo
  const [selectedBlockface, setSelectedBlockface] = useState<Blockface | null>(null);
  const [legalityResult, setLegalityResult] = useState<LegalityResult | null>(null);
  const [showErrorDialog, setShowErrorDialog] = useState(false);
  const [showDemoHint, setShowDemoHint] = useState(true);
  const [blockfaces, setBlockfaces] = useState<Blockface[]>(mockBlockfaces);
  const [isLoadingData, setIsLoadingData] = useState(true);
  const [dataSource, setDataSource] = useState<'mock' | 'sfmta'>('mock');

  // Load SFMTA data on mount
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
        showSuccess(`Loaded ${sfmtaData.length} blockfaces from SFMTA data`);
      } else {
        // Fallback to mock data
        setBlockfaces(mockBlockfaces);
        setDataSource('mock');
        showError('Using demo data - SFMTA data unavailable');
      }
    } catch (error) {
      console.error('Error loading SFMTA data:', error);
      setBlockfaces(mockBlockfaces);
      setDataSource('mock');
      showError('Using demo data - SFMTA data unavailable');
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
    setShowDemoHint(false);
  };

  const handleCloseDetail = () => {
    setSelectedBlockface(null);
    setLegalityResult(null);
  };

  const handleReportError = () => {
    setShowErrorDialog(true);
  };

  return (
    <div className="h-screen w-screen flex flex-col bg-gray-50 overflow-hidden">
      {/* Header */}
      <header className="bg-blue-600 text-white p-4 shadow-md flex-shrink-0">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Curby</h1>
            <p className="text-sm text-blue-100">SF Parking Legality Checker</p>
          </div>
          <div className="text-xs text-blue-100 text-right">
            <div>Mission + SOMA</div>
            <div className="font-semibold">
              {dataSource === 'sfmta' ? 'SFMTA Data' : 'Demo Data'}
            </div>
          </div>
        </div>
      </header>

      {/* Time Controls */}
      <div className="flex-shrink-0">
        <TimeControls
          selectedTime={selectedTime}
          durationMinutes={durationMinutes}
          onTimeChange={setSelectedTime}
          onDurationChange={setDurationMinutes}
        />
      </div>

      {/* Data Source Banner */}
      {dataSource === 'mock' && (
        <div className="bg-amber-50 border-b border-amber-200 px-4 py-2 flex-shrink-0">
          <div className="flex items-center justify-between gap-2 text-xs">
            <div className="flex items-start gap-2 text-amber-900">
              <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
              <p>
                Using demo data. Real SFMTA data unavailable.
              </p>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleRefreshData}
              className="text-amber-900 hover:text-amber-950"
            >
              <RefreshCw className="h-3 w-3 mr-1" />
              Retry
            </Button>
          </div>
        </div>
      )}

      {/* Demo Scenario Banner */}
      <div className="bg-green-50 border-b border-green-200 px-4 py-2 flex-shrink-0">
        <div className="flex items-start gap-2 text-xs text-green-900">
          <Info className="h-4 w-4 mt-0.5 flex-shrink-0" />
          <p>
            <strong>Demo Scenario:</strong> You're at Bryant & 24th St. You need parking for 60 minutes for a nearby meeting. 
            <span className="font-semibold"> Green streets = where to drive!</span>
          </p>
        </div>
      </div>

      {/* Loading Overlay */}
      {isLoadingData && (
        <div className="absolute inset-0 bg-white/80 z-50 flex items-center justify-center">
          <div className="text-center">
            <RefreshCw className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-2" />
            <p className="text-sm text-gray-600">Loading SFMTA parking data...</p>
          </div>
        </div>
      )}

      {/* Map - Takes remaining space */}
      <div className="flex-1 relative min-h-0">
        <MapView
          checkTime={selectedTime}
          durationMinutes={durationMinutes}
          onBlockfaceClick={handleBlockfaceClick}
          blockfaces={blockfaces}
        />
      </div>

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

      {/* Demo Instructions Card */}
      {showDemoHint && !selectedBlockface && !isLoadingData && (
        <div className="absolute bottom-4 right-4 max-w-sm z-20">
          <Card className="p-4 bg-white shadow-xl border-2 border-blue-500">
            <h3 className="font-semibold text-sm text-gray-900 mb-2 flex items-center gap-2">
              🎯 Demo Guide
            </h3>
            <div className="text-xs text-gray-700 space-y-2">
              <p className="font-medium">You're at Bryant & 24th, need 60min parking:</p>
              <ul className="space-y-1 ml-4">
                <li>🟢 <strong>Green = Drive here!</strong> (Legal parking)</li>
                <li>🟡 Yellow = Limited (meters/permits)</li>
                <li>🔴 Red = Illegal (sweeping/tow-away)</li>
              </ul>
              <p className="pt-2 border-t border-gray-200">
                <strong>Try this:</strong> Tap any colored street segment to see parking rules and legality details!
              </p>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};

export default Index;