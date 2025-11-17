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
];

export function SimpleDurationPicker({ durationMinutes, onDurationChange }: SimpleDurationPickerProps) {
  const durationHours = durationMinutes / 60;
  const hourText = durationHours === 1 ? 'hour' : 'hours';

  return (
    <div className="bg-white border-b-2 border-purple-100 p-4 space-y-3 shadow-sm">
      <div className="flex items-center gap-2 mb-2">
        <Clock className="h-5 w-5 text-purple-600" />
        <h2 className="text-base font-bold text-gray-900">
          Find street parking for the next {durationHours} {hourText}
        </h2>
      </div>
      
      <div className="grid grid-cols-3 gap-2">
        {QUICK_DURATIONS.map((duration) => (
          <Button
            key={duration.value}
            variant={durationMinutes === duration.value ? 'default' : 'outline'}
            onClick={() => onDurationChange(duration.value)}
            className={`
              h-auto py-3 px-2 flex flex-col items-center gap-1 rounded-xl border-2 transition-all
              ${durationMinutes === duration.value 
                ? 'bg-gradient-to-br from-purple-600 to-pink-600 border-purple-600 text-white shadow-lg scale-105' 
                : 'border-gray-200 hover:border-purple-300 hover:bg-purple-50'
              }
            `}
          >
            <span className="text-2xl">{duration.emoji}</span>
            <span className="text-xs font-semibold">{duration.label}</span>
          </Button>
        ))}
      </div>

      <div className="text-xs text-gray-600 bg-gradient-to-r from-blue-50 to-purple-50 p-3 rounded-xl border border-purple-100 flex items-center gap-2">
        <span className="text-base">🔍</span>
        <span>
          Looking for parking <strong>right now</strong> for <strong>{durationMinutes / 60}hr</strong>
        </span>
      </div>
    </div>
  );
}