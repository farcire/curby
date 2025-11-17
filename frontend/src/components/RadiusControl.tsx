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
    <div className="fixed bottom-0 left-0 right-0 bg-gray-900 text-gray-100 border-t-2 border-gray-700 z-40 p-4 font-mono">
      <div className="space-y-2">
        <div className="flex items-center justify-between text-sm">
          <span className="flex items-center gap-2">
            🚶 Walking: {radiusBlocks} blocks
          </span>
          <button 
            className="text-gray-400 hover:text-gray-200 text-xs"
            onClick={() => {/* Toggle expanded view */}}
          >
            [▼]
          </button>
        </div>
        
        <div dir="ltr">
          <Slider
            value={[radiusBlocks]}
            onValueChange={(value) => onRadiusChange(value[0])}
            min={1}
            max={8}
            step={1}
            className="w-full"
          />
        </div>
        
        <div className="flex justify-between text-xs text-gray-500">
          <span>1 block</span>
          <span>8 blocks</span>
        </div>
      </div>
    </div>
  );
}