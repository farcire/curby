import { useState, useEffect } from 'react';
import { TimeControls } from '@/components/TimeControls';
import { MapView } from '@/components/MapView';
import { BlockfaceDetail } from '@/components/BlockfaceDetail';
import { ErrorReportDialog } from '@/components/ErrorReportDialog';
import { Blockface, LegalityResult } from '@/types/parking';
import { Card } from '@/components/ui/card';
import { Info } from 'lucide-react';

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
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <header className="bg-blue-600 text-white p-4 shadow-md">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Curby</h1>
            <p className="text-sm text-blue-100">SF Parking Legality Checker</p>
          </div>
          <div className="text-xs text-blue-100 text-right">
            <div>Mission + SOMA</div>
            <div className="font-semibold">MVP Prototype</div>
          </div>
        </div>
      </header>

      {/* Time Controls */}
      <TimeControls
        selectedTime={selectedTime}
        durationMinutes={durationMinutes}
        onTimeChange={setSelectedTime}
        onDurationChange={setDurationMinutes}
      />

      {/* Demo Scenario Banner */}
      <div className="bg-green-50 border-b border-green-200 px-4 py-2">
        <div className="flex items-start gap-2 text-xs text-green-900">
          <Info className="h-4 w-4 mt-0.5 flex-shrink-0" />
          <p>
            <strong>Demo Scenario:</strong> You're at Bryant & 24th St. You need parking for 60 minutes for a nearby meeting. 
            <span className="font-semibold"> Green streets = where to drive!</span>
          </p>
        </div>
      </div>

      {/* Map */}
      <div className="flex-1 relative">
        <MapView
          checkTime={selectedTime}
          durationMinutes={durationMinutes}
          onBlockfaceClick={handleBlockfaceClick}
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
      {showDemoHint && !selectedBlockface && (
        <div className="absolute bottom-4 right-4 max-w-sm">
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
                <strong>Try this:</strong> Tap the red Bryant St segment (south of you) to see why it's illegal right now!
              </p>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};

export default Index;