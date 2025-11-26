import { Slider } from '@/components/ui/slider';
import { Logo } from '@/components/Logo';

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
    <div className="fixed bottom-0 left-0 right-0 z-40 p-4 pointer-events-none flex justify-center">
      <div className="bg-gradient-to-r from-purple-600 via-pink-600 to-orange-500 text-white shadow-2xl rounded-2xl p-4 w-full max-w-md pointer-events-auto mb-4 mx-4">
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="bg-white/20 p-2 rounded-xl">
                <Logo size="sm" animated={true} />
              </div>
              <div>
                <div className="text-xs font-semibold opacity-90 uppercase tracking-wider">Search Radius</div>
                <div className="text-xl font-bold">{radiusBlocks} {radiusBlocks === 1 ? 'block' : 'blocks'}</div>
              </div>
            </div>
          </div>
          
          <div className="space-y-1">
            <div dir="ltr" className="relative touch-none">
              <Slider
                value={[radiusBlocks]}
                onValueChange={(value) => onRadiusChange(value[0])}
                min={1}
                max={8}
                step={1}
                className="w-full [&_[role=slider]]:bg-white [&_[role=slider]]:border-4 [&_[role=slider]]:border-purple-500 [&_[role=slider]]:shadow-lg [&_[role=slider]]:h-6 [&_[role=slider]]:w-6 [&_[role=slider]]:transition-transform [&_[role=slider]]:active:scale-110 [&_.relative]:h-3 [&_.relative]:bg-white/30 [&_.relative]:rounded-full [&_[data-orientation=horizontal]]:bg-white [&_[data-orientation=horizontal]]:rounded-full"
              />
            </div>
            <div className="flex justify-between text-[10px] font-bold text-white/80 uppercase tracking-wider">
              <span>Quick (1)</span>
              <span>Stroll (8)</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}