import { Button } from '@/components/ui/button';
import { Clock } from 'lucide-react';

interface SimpleDurationPickerProps {
  durationMinutes: number;
  onDurationChange: (minutes: number) => void;
}

const QUICK_DURATIONS = [
  { value: 60, label: '1 hour', emoji: '☕' },
  { value: 120, label: '2 hours', emoji: '🍽️' },
  { value: 180, label: '3 hours', emoji: '🛍️' },
  { value: 360, label: '6 hours', emoji: '🎬' },
  { value: 720, label: '12 hours', emoji: '🌙' },
  { value: 1440, label: '24 hours', emoji: '📅' },
];

export function SimpleDurationPicker({ durationMinutes, onDurationChange }: SimpleDurationPickerProps) {
  const durationHours = durationMinutes / 60;
  const hourText = durationHours === 1 ? 'hour' : 'hours';

  return (
    <div className="bg-white border-b border-purple-100 px-3 py-2 shadow-sm z-10 relative">
      <div className="flex items-center gap-2 mb-2">
        <Clock className="h-3 w-3 text-purple-600" />
        <h2 className="text-xs font-bold text-gray-900">
          Duration: <span className="text-purple-700">{durationHours} {hourText}</span>
        </h2>
      </div>
      
      <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-hide -mx-1 px-1">
        {QUICK_DURATIONS.map((duration) => (
          <Button
            key={duration.value}
            variant={durationMinutes === duration.value ? 'default' : 'outline'}
            onClick={() => onDurationChange(duration.value)}
            className={`
              h-8 px-3 flex-shrink-0 flex items-center gap-1.5 rounded-full border transition-all text-xs
              ${durationMinutes === duration.value
                ? 'bg-gradient-to-r from-purple-600 to-pink-600 border-transparent text-white shadow-sm'
                : 'border-gray-200 hover:border-purple-300 hover:bg-purple-50 text-gray-700'
              }
            `}
          >
            <span className="text-sm">{duration.emoji}</span>
            <span className="font-medium">{duration.label}</span>
          </Button>
        ))}
      </div>
    </div>
  );
}