import { useState } from 'react';
import { TimeControls } from '@/components/TimeControls';
import { MapView } from '@/components/MapView';
import { BlockfaceDetail } from '@/components/BlockfaceDetail';
import { ErrorReportDialog } from '@/components/ErrorReportDialog';
import { Blockface, LegalityResult } from '@/types/parking';
import { Card } from '@/components/ui/card';
import { Info } from 'lucide-react';

const Index = () => {
  const [selectedTime, setSelectedTime] = useState(new Date());
  const [durationMinutes, setDurationMinutes] = useState(120); // Default 2 hours
  const [selectedBlockface, setSelectedBlockface] = useState<Blockface | null>(null);
  const [legalityResult, setLegalityResult] = useState<LegalityResult | null>(null);
  const [showErrorDialog, setShowErrorDialog] = useState(false);

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

      {/* Info Banner */}
      <div className="bg-amber-50 border-b border-amber-200 px-4 py-2">
        <div className="flex items-start gap-2 text-xs text-amber-900">
          <Info className="h-4 w-4 mt-0.5 flex-shrink-0" />
          <p>
            <strong>Prototype Demo:</strong> This is a frontend prototype with mock data. 
            Tap any colored street segment to see parking rules. Real implementation requires backend integration.
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

      {/* Instructions Card (shown when no blockface selected) */}
      {!selectedBlockface && (
        <div className="absolute bottom-4 right-4 max-w-sm">
          <Card className="p-4 bg-white shadow-xl">
            <h3 className="font-semibold text-sm text-gray-900 mb-2">
              How to Use Curby
            </h3>
            <ol className="text-xs text-gray-700 space-y-1 list-decimal list-inside">
              <li>Adjust the date, time, and parking duration above</li>
              <li>Colored lines show parking legality:
                <ul className="ml-4 mt-1 space-y-0.5">
                  <li>🟢 Green = Legal to park</li>
                  <li>🟡 Yellow = Limited (meters, time limits)</li>
                  <li>🔴 Red = Illegal (sweeping, tow-away)</li>
                  <li>⚫ Gray = Insufficient data</li>
                </ul>
              </li>
              <li>Tap any street segment to see detailed rules</li>
              <li>Report errors to help improve accuracy</li>
            </ol>
          </Card>
        </div>
      )}
    </div>
  );
};

export default Index;