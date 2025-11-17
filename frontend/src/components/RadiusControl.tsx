import { Slider } from '@/components/ui/slider';
import { Card } from '@/components/ui/card';
import { MapPin, Navigation2 } from 'lucide-react';

interface RadiusControlProps {
  radiusBlocks: number;
  onRadiusChange: (blocks: number) => void;
  legalBlocksInRadius: number;
  totalBlocksInRadius: number;
  nearestLegalDistance?: number;
  nearestLegalStreet?: string;
}

export function RadiusControl({
  radiusBlocks,
  onRadiusChange,
  legalBlocksInRadius,
  totalBlocksInRadius,
  nearestLegalDistance,
  nearestLegalStreet,
}: RadiusControlProps) {
  const radiusMeters = radiusBlocks * 110; // ~110m per block
  const blockText = radiusBlocks === 1 ? 'block' : 'blocks';

  return (
    <Card className="fixed bottom-0 left-0 right-0 bg-white border-t-2 border-purple-200 shadow-2xl rounded-t-3xl z-40 p-4 space-y-3">
      {/* Radius Slider */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <MapPin className="h-5 w-5 text-purple-600" />
            <span className="text-sm font-bold text-gray-900">
              Walking distance: {radiusBlocks} {blockText}
            </span>
          </div>
          <span className="text-xs text-gray-500">~{radiusMeters}m</span>
        </div>
        
        <Slider
          value={[radiusBlocks]}
          onValueChange={(value) => onRadiusChange(value[0])}
          min={1}
          max={5}
          step={1}
          className="w-full"
        />
        
        <div className="flex justify-between text-xs text-gray-500">
          <span>1 block</span>
          <span>3 blocks</span>
          <span>5 blocks</span>
        </div>
      </div>

      {/* Status Info */}
      <div className="pt-2 border-t border-gray-100">
        {legalBlocksInRadius > 0 ? (
          <div className="flex items-center gap-2 text-sm">
            <span className="text-2xl">✅</span>
            <span className="text-gray-900">
              <strong>{legalBlocksInRadius}</strong> of {totalBlocksInRadius} blocks available for parking
            </span>
          </div>
        ) : nearestLegalStreet && nearestLegalDistance ? (
          <div className="bg-gradient-to-r from-amber-50 to-orange-50 rounded-xl p-3 border border-amber-200">
            <div className="flex items-start gap-3">
              <Navigation2 className="h-5 w-5 text-amber-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm font-semibold text-amber-900 mb-1">
                  No parking within {radiusBlocks} {blockText}
                </p>
                <p className="text-xs text-amber-800">
                  Nearest available: <strong>{nearestLegalStreet}</strong> (~{Math.round(nearestLegalDistance)}m away)
                </p>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <span className="text-2xl">🔍</span>
            <span>Checking {totalBlocksInRadius} blocks in your area...</span>
          </div>
        )}
      </div>
    </Card>
  );
}