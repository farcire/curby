import { useState, useEffect } from 'react';
import { TimeControls } from '@/components/TimeControls';
import { MapView } from '@/components/MapView';
import { BlockfaceDetail } from '@/components/BlockfaceDetail';
import { ErrorReportDialog } from '@/components/ErrorReportDialog';
import { Blockface, LegalityResult } from '@/types/parking';
import { Card } from '@/components/ui/card';
import { Sparkles, MapPin, RefreshCw, PartyPopper } from 'lucide-react';
import { fetchSFMTABlockfaces, clearSFMTACache } from '@/utils/sfmtaDataFetcher';
import { mockBlockfaces } from '@/data/mockBlockfaces';
import { Button } from '@/components/ui/button';
import { showSuccess, showError } from '@/utils/toast';

const Index = () => {
  // Demo scenario: Monday at 12:00 PM, need 60 minutes of parking
  const getDemoTime = () => {
    const now = new Date();
    const demo = new Date(now);
    demo.setHours(12, 0, 0, 0);
    const dayOfWeek = demo.getDay();
    const daysUntilMonday = dayOfWeek === 1 ? 0 : (8 - dayOfWeek) % 7;
    demo.setDate(demo.getDate() + daysUntilMonday);
    return demo;
  };

  const [selectedTime, setSelectedTime] = useState(getDemoTime());
  const [durationMinutes, setDurationMinutes] = useState(60);
  const [selectedBlockface, setSelectedBlockface] = useState<Blockface | null>(null);
  const [legalityResult, setLegalityResult] = useState<LegalityResult | null>(null);
  const [showErrorDialog, setShowErrorDialog] = useState(false);
  const [showDemoHint, setShowDemoHint] = useState(true);
  const [blockfaces, setBlockfaces] = useState<Blockface[]>(mockBlockfaces);
  const [isLoadingData, setIsLoadingData] = useState(true);
  const [dataSource, setDataSource] = useState<'mock' | 'sfmta'>('mock');
  const [celebrateFind, setCelebrateFind] = useState(false);

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
        showSuccess(`🎉 Found ${sfmtaData.length} parking spots to explore!`);
      } else {
        setBlockfaces(mockBlockfaces);
        setDataSource('mock');
        showError('Using demo data for now - real data coming soon!');
      }
    } catch (error) {
      console.error('Error loading SFMTA data:', error);
      setBlockfaces(mockBlockfaces);
      setDataSource('mock');
      showError('Using demo data for now - real data coming soon!');
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
    
    // Celebrate when finding a legal spot!
    if (result.status === 'legal') {
      setCelebrateFind(true);
      setTimeout(() => setCelebrateFind(false), 2000);
    }
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
      {/* Whimsical Header */}
      <header className="bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 text-white p-4 shadow-lg flex-shrink-0 relative overflow-hidden">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-0 left-0 w-32 h-32 bg-white rounded-full -translate-x-16 -translate-y-16"></div>
          <div className="absolute bottom-0 right-0 w-40 h-40 bg-white rounded-full translate-x-20 translate-y-20"></div>
        </div>
        <div className="relative flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-white/20 backdrop-blur-sm rounded-2xl p-2">
              <MapPin className="h-6 w-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold flex items-center gap-2">
                Curby
                <Sparkles className="h-5 w-5 animate-pulse" />
              </h1>
              <p className="text-sm text-white/90">Your parking sidekick ✨</p>
            </div>
          </div>
          <div className="text-xs text-white/90 text-right bg-white/10 backdrop-blur-sm rounded-xl px-3 py-2">
            <div className="font-semibold">Mission + SOMA</div>
            <div className="flex items-center gap-1 justify-end">
              {dataSource === 'sfmta' ? '🌟 Live Data' : '🎭 Demo Mode'}
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

      {/* Playful Data Source Banner */}
      {dataSource === 'mock' && (
        <div className="bg-gradient-to-r from-amber-50 to-orange-50 border-b border-amber-200 px-4 py-3 flex-shrink-0">
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-start gap-3 text-sm text-amber-900">
              <span className="text-2xl">🎪</span>
              <div>
                <p className="font-semibold">Demo Mode Active!</p>
                <p className="text-xs text-amber-800">
                  We're showing you sample data while we fetch the real stuff
                </p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleRefreshData}
              className="text-amber-900 hover:text-amber-950 hover:bg-amber-100 rounded-full"
            >
              <RefreshCw className="h-4 w-4 mr-1" />
              Try Again
            </Button>
          </div>
        </div>
      )}

      {/* Story-driven Demo Scenario */}
      <div className="bg-gradient-to-r from-green-50 to-emerald-50 border-b border-green-200 px-4 py-3 flex-shrink-0">
        <div className="flex items-start gap-3">
          <span className="text-2xl">🎯</span>
          <div className="flex-1">
            <p className="text-sm text-green-900 leading-relaxed">
              <strong className="font-semibold">Your Mission:</strong> You're meeting a friend at Bryant & 24th St in an hour. 
              You need parking for 60 minutes. 
              <span className="inline-flex items-center gap-1 ml-1 font-semibold text-green-700">
                Follow the green streets to victory! 🌟
              </span>
            </p>
          </div>
        </div>
      </div>

      {/* Celebration Overlay */}
      {celebrateFind && (
        <div className="fixed inset-0 pointer-events-none z-50 flex items-center justify-center">
          <div className="animate-bounce">
            <PartyPopper className="h-24 w-24 text-green-500" />
          </div>
        </div>
      )}

      {/* Loading with Personality */}
      {isLoadingData && (
        <div className="absolute inset-0 bg-gradient-to-br from-blue-50/95 via-purple-50/95 to-pink-50/95 backdrop-blur-sm z-50 flex items-center justify-center">
          <div className="text-center">
            <div className="relative">
              <MapPin className="h-16 w-16 text-purple-600 mx-auto mb-4 animate-bounce" />
              <Sparkles className="h-6 w-6 text-pink-500 absolute top-0 right-0 animate-pulse" />
            </div>
            <p className="text-lg font-semibold text-gray-900 mb-2">Finding parking spots...</p>
            <p className="text-sm text-gray-600">✨ Sprinkling some magic on the data ✨</p>
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

      {/* Whimsical Demo Guide */}
      {showDemoHint && !selectedBlockface && !isLoadingData && (
        <div className="absolute bottom-6 right-6 max-w-sm z-20 animate-in slide-in-from-bottom-4 duration-500">
          <Card className="p-5 bg-white shadow-2xl border-2 border-purple-300 rounded-2xl relative overflow-hidden">
            <div className="absolute top-0 right-0 w-20 h-20 bg-gradient-to-br from-purple-200 to-pink-200 rounded-full -translate-y-10 translate-x-10 opacity-50"></div>
            <div className="relative">
              <div className="flex items-center gap-2 mb-3">
                <span className="text-2xl">🗺️</span>
                <h3 className="font-bold text-base text-gray-900">Your Parking Adventure Awaits!</h3>
              </div>
              <div className="text-sm text-gray-700 space-y-3">
                <p className="font-medium text-purple-900">
                  Tap any colored street to discover its parking secrets:
                </p>
                <div className="space-y-2 ml-2">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-2 bg-green-500 rounded-full"></div>
                    <span><strong>Green</strong> = Park here! 🎉</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-2 bg-amber-500 rounded-full"></div>
                    <span><strong>Yellow</strong> = Possible (with limits)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-2 bg-red-500 rounded-full"></div>
                    <span><strong>Red</strong> = Nope! Keep driving</span>
                  </div>
                </div>
                <div className="pt-3 border-t border-purple-100 bg-purple-50 -mx-5 -mb-5 px-5 py-3 rounded-b-2xl">
                  <p className="text-xs text-purple-900 flex items-center gap-2">
                    <Sparkles className="h-4 w-4" />
                    <span>Pro tip: Green streets are your best friends!</span>
                  </p>
                </div>
              </div>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};

export default Index;