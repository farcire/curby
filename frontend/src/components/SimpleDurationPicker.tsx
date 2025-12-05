import { Slider } from '@/components/ui/slider';

interface SimpleDurationPickerProps {
  durationMinutes: number;
  onDurationChange: (minutes: number) => void;
  showFreeOnly: boolean;
  onToggleFreeOnly: () => void;
}

export function SimpleDurationPicker({
  durationMinutes,
  onDurationChange,
  showFreeOnly,
  onToggleFreeOnly,
}: SimpleDurationPickerProps) {
  
  const steps = [
    60, 120, 180, 240, 300, 360, 480, 600, 720, 960, 1200, 1440,
  ];

  const maxStep = steps.length - 1;

  const stepToMinutes = (step: number) => {
    return steps[Math.min(step, maxStep)];
  };

  const minutesToStep = (minutes: number) => {
    let closestStep = 0;
    let minDiff = Infinity;
    
    steps.forEach((val, index) => {
        const diff = Math.abs(val - minutes);
        if (diff < minDiff) {
            minDiff = diff;
            closestStep = index;
        }
    });
    return closestStep;
  };

  const formatDuration = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    return `${hours}h`;
  };

  const getDurationEmoji = (minutes: number) => {
    if (minutes <= 60) return '☕';
    if (minutes <= 120) return '🍽️';
    if (minutes <= 180) return '🛍️';
    if (minutes <= 360) return '🎬';
    if (minutes <= 720) return '💼';
    return '🌙';
  };

  const sliderValue = minutesToStep(durationMinutes);

  const ticks = [
    { label: '1h', stepIndex: 0 },
    { label: '3h', stepIndex: 2 },
    { label: '6h', stepIndex: 5 },
    { label: '12h', stepIndex: 8 },
    { label: '24h', stepIndex: 11 },
  ];

  return (
    <div className="fixed bottom-6 left-0 right-0 z-40 px-4 pointer-events-none flex justify-center">
      <div className="bg-gradient-to-r from-purple-600/95 via-pink-600/95 to-orange-500/95 backdrop-blur-sm text-white shadow-xl rounded-full px-6 pt-1.5 pb-3 w-full max-w-sm pointer-events-auto">
        <div className="space-y-0">
          {/* Top Row: Duration */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1">
              <span className="text-sm font-bold">{formatDuration(durationMinutes)}</span>
              <span className="text-[10px] font-semibold opacity-90 uppercase tracking-wider">Parking</span>
              <span className="text-base ml-1">{getDurationEmoji(durationMinutes)}</span>
            </div>
            {/* Free Only Checkbox */}
            <button
              onClick={onToggleFreeOnly}
              className="flex items-center gap-1.5 flex-shrink-0"
              title={showFreeOnly ? "Showing free parking only" : "Showing all parking"}
            >
              <div className={`
                w-3.5 h-3.5 rounded border-2 flex items-center justify-center transition-all
                ${showFreeOnly
                  ? 'bg-white border-white'
                  : 'bg-transparent border-white/60'
                }
              `}>
                {showFreeOnly && (
                  <svg className="w-2.5 h-2.5 text-purple-600" fill="none" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" viewBox="0 0 24 24" stroke="currentColor">
                    <path d="M5 13l4 4L19 7"></path>
                  </svg>
                )}
              </div>
              <span className={`text-[10px] font-semibold uppercase tracking-wider transition-all ${
                showFreeOnly ? 'opacity-100 text-white' : 'opacity-60 text-white/70'
              }`}>Free only</span>
            </button>
          </div>
          
          {/* Bottom Row: Slider */}
          <div className="flex items-center">
            
            {/* Slider Section */}
            <div className="flex-1 min-w-0">
              <div className="relative pb-4 pt-0">
                <Slider
                  value={[sliderValue]}
                  onValueChange={(vals) => onDurationChange(stepToMinutes(vals[0]))}
                  min={0}
                  max={maxStep}
                  step={1}
                  className="w-full cursor-pointer [&_[role=slider]]:bg-white [&_[role=slider]]:border-2 [&_[role=slider]]:border-purple-500 [&_[role=slider]]:shadow-sm [&_[role=slider]]:h-4 [&_[role=slider]]:w-4 [&_[role=slider]]:transition-transform [&_[role=slider]]:active:scale-125 [&_.relative]:h-1.5 [&_.relative]:bg-white/30 [&_.relative]:rounded-full [&_[data-orientation=horizontal]]:bg-white [&_[data-orientation=horizontal]]:rounded-full"
                />
                
                {/* Labels */}
                <div className="absolute top-3 left-0 right-0 h-3 text-[9px] font-medium opacity-80 pointer-events-none select-none">
                    {ticks.map((tick) => (
                        <div 
                            key={tick.label}
                            className="absolute transform -translate-x-1/2 text-center whitespace-nowrap"
                            style={{ left: `${(tick.stepIndex / maxStep) * 100}%` }}
                        >
                            {tick.label}
                        </div>
                    ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}