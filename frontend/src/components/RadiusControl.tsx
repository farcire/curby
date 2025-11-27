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
    <div className="fixed bottom-6 left-0 right-0 z-40 px-4 pointer-events-none flex justify-center">
      <div className="bg-gradient-to-r from-purple-600/95 via-pink-600/95 to-orange-500/95 backdrop-blur-sm text-white shadow-xl rounded-full px-5 py-3 w-full max-w-sm pointer-events-auto flex items-center gap-4">
        <div className="flex-shrink-0 min-w-[80px]">
          <div className="text-[10px] font-semibold opacity-90 uppercase tracking-wider leading-none mb-0.5">Radius</div>
          <div className="text-sm font-bold leading-none">{radiusBlocks} {radiusBlocks === 1 ? 'block' : 'blocks'}</div>
        </div>
        
        <div className="flex-1 min-w-0">
          <div dir="ltr" className="relative touch-none flex items-center h-full">
            <Slider
              value={[radiusBlocks]}
              onValueChange={(value) => onRadiusChange(value[0])}
              min={1}
              max={8}
              step={1}
              className="w-full cursor-pointer [&_[role=slider]]:bg-white [&_[role=slider]]:border-2 [&_[role=slider]]:border-purple-500 [&_[role=slider]]:shadow-sm [&_[role=slider]]:h-4 [&_[role=slider]]:w-4 [&_[role=slider]]:transition-transform [&_[role=slider]]:active:scale-125 [&_.relative]:h-1.5 [&_.relative]:bg-white/30 [&_.relative]:rounded-full [&_[data-orientation=horizontal]]:bg-white [&_[data-orientation=horizontal]]:rounded-full"
            />
          </div>
        </div>
      </div>
    </div>
  );
}