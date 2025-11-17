import { Slider } from '@/components/ui/slider';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Navigation2 } from 'lucide-react';
import { format } from 'date-fns';

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

const DURATION_OPTIONS = [
  { value: 60, label: '1 hr' },
  { value: 120, label: '2 hrs' },
  { value: 180, label: '3 hrs' },
  { value: 360, label: '6 hrs' },
  { value: 720, label: '12 hrs' },
  { value: 1440, label: '24 hrs' },
];

const TIME_OPTIONS = [
  { value: 'now', label: 'Now' },
  { value: '1h', label: 'In 1 hour' },
  { value: '2h', label: 'In 2 hours' },
  { value: '4h', label: 'In 4 hours' },
  { value: 'tomorrow', label: 'Tomorrow' },
];

export function RadiusControl({
  radiusBlocks,
  onRadiusChange,
  legalBlocksInRadius,
  totalBlocksInRadius,
  nearestLegalDistance,
  nearestLegalStreet,
  selectedTime,
  durationMinutes,
  onTimeChange,
  onDurationChange,
}: RadiusControlProps) {
  const walkMinutes = Math.round((radiusBlocks * 110) / 80); // ~80m/min walking speed

  const handleTimeSelect = (value: string) => {
    const now = new Date();
    switch (value) {
      case 'now':
        onTimeChange(now);
        break;
      case '1h':
        onTimeChange(new Date(now.getTime() + 60 * 60 * 1000));
        break;
      case '2h':
        onTimeChange(new Date(now.getTime() + 2 * 60 * 60 * 1000));
        break;
      case '4h':
        onTimeChange(new Date(now.getTime() + 4 * 60 * 60 * 1000));
        break;
      case 'tomorrow':
        const tomorrow = new Date(now);
        tomorrow.setDate(tomorrow.getDate() + 1);
        tomorrow.setHours(9, 0, 0, 0);
        onTimeChange(tomorrow);
        break;
    }
  };

  const isNow = Math.abs(selectedTime.getTime() - new Date().getTime()) < 60000;

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-gray-900 text-gray-100 border-t-2 border-gray-700 z-40 p-4 space-y-4 font-mono">
      {/* Walking Distance Slider */}
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
        
        <Slider
          value={[radiusBlocks]}
          onValueChange={(value) => onRadiusChange(value[0])}
          min={1}
          max={8}
          step={1}
          className="w-full"
        />
        
        <div className="flex justify-between text-xs text-gray-500">
          <span>1</span>
          <span>2</span>
          <span>3</span>
          <span>5</span>
          <span>8</span>
        </div>

        {/* Status Info */}
        <div className="text-sm text-gray-400">
          {legalBlocksInRadius > 0 ? (
            <span>{legalBlocksInRadius} spots • ~{walkMinutes} min walk</span>
          ) : nearestLegalStreet && nearestLegalDistance ? (
            <div className="flex items-center gap-2 text-amber-400">
              <Navigation2 className="h-4 w-4" />
              <span>Nearest: {nearestLegalStreet} (~{Math.round(nearestLegalDistance)}m)</span>
            </div>
          ) : (
            <span>Checking {totalBlocksInRadius} blocks...</span>
          )}
        </div>
      </div>

      {/* Time and Duration Controls */}
      <div className="flex items-center gap-3 pt-3 border-t border-gray-800">
        <Select value={isNow ? 'now' : 'custom'} onValueChange={handleTimeSelect}>
          <SelectTrigger className="w-32 bg-gray-800 border-gray-700 text-gray-100 font-mono text-sm">
            <SelectValue placeholder="Now" />
          </SelectTrigger>
          <SelectContent className="bg-gray-800 border-gray-700 text-gray-100 font-mono">
            {TIME_OPTIONS.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select 
          value={durationMinutes.toString()} 
          onValueChange={(val) => onDurationChange(parseInt(val))}
        >
          <SelectTrigger className="flex-1 bg-gray-800 border-gray-700 text-gray-100 font-mono text-sm">
            <span>Duration: <SelectValue /></span>
          </SelectTrigger>
          <SelectContent className="bg-gray-800 border-gray-700 text-gray-100 font-mono">
            {DURATION_OPTIONS.map((option) => (
              <SelectItem key={option.value} value={option.value.toString()}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    </div>
  );
}