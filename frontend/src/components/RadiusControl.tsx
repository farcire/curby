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
    <div className="fixed bottom-0 left-0 right-0 bg-gradient-to-r from-purple-600 via-pink-600 to-orange-500 text-white z-40 p-3 shadow-2xl">
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Logo size="sm" animated={true} />
            <div>
              <div className="text-xs font-semibold opacity-90">Walking Distance</div>
              <div className="text-lg font-bold">{radiusBlocks} {radiusBlocks === 1 ? 'block' : 'blocks'}</div>
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
            className="w-full [&_[role=slider]]:bg-white [&_[role=slider]]:border-4 [&_[role=slider]]:border-purple-300 [&_[role=slider]]:shadow-lg [&_[role=slider]]:h-5 [&_[role=slider]]:w-5 [&_.relative]:h-2 [&_.relative]:bg-white/30 [&_.relative]:rounded-full [&_[data-orientation=horizontal]]:bg-white [&_[data-orientation=horizontal]]:rounded-full"
          />
        </div>
        
        <div className="flex justify-between text-xs font-semibold text-white/90">
          <span>Quick (1)</span>
          <span>Stroll (8)</span>
        </div>
      </div>
    </div>
  );
}