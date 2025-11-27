import { Slider } from '@/components/ui/slider';

interface SimpleDurationPickerProps {
  durationMinutes: number;
  onDurationChange: (minutes: number) => void;
}

export function SimpleDurationPicker({
  durationMinutes,
  onDurationChange,
}: SimpleDurationPickerProps) {
  
  // Custom non-linear scale logic
  // Steps 0-6: 1h increments (1h to 7h)
  // Steps 7-12: ~3h increments (10h, 13h, 16h, 19h, 21h, 24h)
  // But to make it smoother for 1, 2, 3, 6 emphasis:
  // Let's use a mapping array
  const steps = [
    60,   // 0: 1h
    120,  // 1: 2h
    180,  // 2: 3h
    240,  // 3: 4h
    300,  // 4: 5h
    360,  // 5: 6h
    480,  // 6: 8h
    600,  // 7: 10h
    720,  // 8: 12h
    960,  // 9: 16h
    1200, // 10: 20h
    1440, // 11: 24h
  ];

  const maxStep = steps.length - 1;

  // Map internal slider step (0-11) to minutes
  const stepToMinutes = (step: number) => {
    return steps[Math.min(step, maxStep)];
  };

  // Map minutes to internal slider step
  const minutesToStep = (minutes: number) => {
    // Find closest step
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
    if (minutes <= 60) return '☕'; // Coffee/Quick
    if (minutes <= 120) return '🍽️'; // Meal
    if (minutes <= 180) return '🛍️'; // Shopping
    if (minutes <= 360) return '🎬'; // Event
    if (minutes <= 720) return '💼'; // Work
    return '🌙'; // Overnight/Long
  };

  const sliderValue = minutesToStep(durationMinutes);

  // Define ticks based on step indices
  const ticks = [
    { label: '1h', stepIndex: 0 },
    { label: '3h', stepIndex: 2 },
    { label: '6h', stepIndex: 5 },
    { label: '12h', stepIndex: 8 },
    { label: '24h', stepIndex: 11 },
  ];

  return (
    <div className="fixed bottom-6 left-0 right-0 z-40 px-4 pointer-events-none flex justify-center">
      {/* Pill Container */}
      <div className="bg-gradient-to-r from-purple-600/95 via-pink-600/95 to-orange-500/95 backdrop-blur-sm text-white shadow-xl rounded-full px-5 py-3 w-full max-w-sm pointer-events-auto flex items-center gap-4">
        {/* Label Section */}
        <div className="flex-shrink-0 min-w-[80px]">
          <div className="text-[10px] font-semibold opacity-90 uppercase tracking-wider leading-none mb-0.5">I'm parking for</div>
          <div className="text-sm font-bold leading-none flex items-center gap-1.5">
            <span>{formatDuration(durationMinutes)}</span>
            <span className="text-base animate-pulse-slow">{getDurationEmoji(durationMinutes)}</span>
          </div>
        </div>
        
        {/* Slider Section */}
        <div className="flex-1 min-w-0">
          <div className="relative pb-4 pt-1">
            <div dir="ltr" className="relative touch-none flex items-center h-full z-10">
              <Slider
                value={[sliderValue]}
                onValueChange={(vals) => onDurationChange(stepToMinutes(vals[0]))}
                min={0}
                max={maxStep}
                step={1}
                className="w-full cursor-pointer [&_[role=slider]]:bg-white [&_[role=slider]]:border-2 [&_[role=slider]]:border-purple-500 [&_[role=slider]]:shadow-sm [&_[role=slider]]:h-4 [&_[role=slider]]:w-4 [&_[role=slider]]:transition-transform [&_[role=slider]]:active:scale-125 [&_.relative]:h-1.5 [&_.relative]:bg-white/30 [&_.relative]:rounded-full [&_[data-orientation=horizontal]]:bg-white [&_[data-orientation=horizontal]]:rounded-full"
              />
            </div>
            
            {/* Labels */}
            <div className="absolute top-5 left-0 right-0 h-3 text-[9px] font-medium opacity-80 pointer-events-none select-none">
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
  );
}