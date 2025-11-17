import { Slider } from '@/components/ui/slider';

interface RadiusControlProps {
  radiusBlocks: number;
  onRadiusChange: (blocks: number) => void;
  legalBlocksInRadius: number;
  totalBlocksInRadius: number;
  nearestLegalDistance?: number;
  nearestLegalStreet?: string;
  selectedTime: Date;
  durationMinutes: number;
  onTimeChange: (time: Date) => void;
  onDurationChange: (minutes: number) => void;
}

export function RadiusControl({
  radiusBlocks,
  onRadiusChange,
}: RadiusControlProps) {
  return (
    <div className="fixed bottom-0 left-0 right-0 bg-gradient-to-r from-purple-600 via-pink-600 to-orange-500 text-white z-40 p-6 shadow-2xl">
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-3xl animate-bounce">🚶</span>
            <div>
              <div className="text-sm font-semibold opacity-90">Walking Distance</div>
              <div className="text-2xl font-bold">{radiusBlocks} {radiusBlocks === 1 ? 'block' : 'blocks'}</div>
            </div>
          </div>
        </div>
        
        <div dir="ltr" className="relative">
          <Slider
            value={[radiusBlocks]}
            onValueChange={(value) => onRadiusChange(value[0])}
            min={1}
            max={8}
            step={1}
            className="w-full [&_[role=slider]]:bg-white [&_[role=slider]]:border-4 [&_[role=slider]]:border-purple-300 [&_[role=slider]]:shadow-lg [&_[role=slider]]:h-6 [&_[role=slider]]:w-6 [&_.relative]:h-3 [&_.relative]:bg-white/30 [&_.relative]:rounded-full [&_[data-orientation=horizontal]]:bg-white [&_[data-orientation=horizontal]]:rounded-full"
          />
        </div>
        
        <div className="flex justify-between text-sm font-semibold text-white/90">
          <span>🏃 Quick (1)</span>
          <span>🚶‍♂️ Stroll (8)</span>
        </div>
      </div>
    </div>
  );
}