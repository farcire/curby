import { Blockface, LegalityResult } from '@/types/parking';
import { format, addDays, getDay, differenceInHours, differenceInMinutes } from 'date-fns';
import { X, Clock, MapPin, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface BlockfaceDetailProps {
  blockface: Blockface;
  legalityResult: LegalityResult;
  onReportError: () => void;
  onClose: () => void;
}

export function BlockfaceDetail({ blockface, legalityResult, onReportError, onClose }: BlockfaceDetailProps) {
  const getStatusConfig = () => {
    switch (legalityResult.status) {
      case 'legal':
        return { 
          gradient: 'from-green-500 to-emerald-600',
          emoji: '✅',
          text: 'You can park here'
        };
      case 'illegal':
        return { 
          gradient: 'from-red-500 to-rose-600',
          emoji: '🚫',
          text: "Don't park here"
        };
      case 'insufficient-data':
        return { 
          gradient: 'from-gray-500 to-slate-600',
          emoji: '🤔',
          text: 'Check signs on-site'
        };
    }
  };

  // Calculate next restriction
  const getNextRestriction = () => {
    const now = new Date();
    const currentDay = getDay(now);
    
    const upcomingRestrictions = blockface.rules
      .filter(rule => rule.type === 'street-sweeping' || rule.type === 'no-parking' || rule.type === 'tow-away')
      .flatMap(rule => {
        return rule.timeRanges.map(range => {
          const daysUntil = range.daysOfWeek.map(day => {
            let diff = day - currentDay;
            if (diff <= 0) diff += 7;
            return { day, diff };
          }).sort((a, b) => a.diff - b.diff);

          if (daysUntil.length === 0) return null;

          const nextOccurrence = addDays(now, daysUntil[0].diff);
          const [hours, minutes] = range.startTime.split(':').map(Number);
          nextOccurrence.setHours(hours, minutes, 0, 0);

          return {
            rule,
            date: nextOccurrence,
            timeRange: range,
          };
        }).filter(Boolean);
      })
      .filter(Boolean)
      .sort((a, b) => a!.date.getTime() - b!.date.getTime());

    return upcomingRestrictions[0] || null;
  };

  const nextRestriction = getNextRestriction();

  const getDayName = (date: Date) => {
    const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    return days[getDay(date)];
  };

  const status = getStatusConfig();

  return (
    <div className="fixed inset-x-0 bottom-0 z-50 flex justify-center p-3 pointer-events-none">
      <div className="w-full max-w-sm pointer-events-auto animate-in slide-in-from-bottom-4 duration-300 shadow-2xl rounded-xl overflow-hidden">
        {/* Status Header */}
        <div className={`bg-gradient-to-r ${status.gradient} text-white px-3 py-2 flex items-center justify-between`}>
          <div className="flex items-center gap-2">
            <span className="text-lg">{status.emoji}</span>
            <span className="text-sm font-bold">{status.text}</span>
          </div>
          <button 
            onClick={onClose}
            className="text-white/80 hover:text-white bg-white/20 hover:bg-white/30 rounded-full p-1 transition-all"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>

        {/* Content */}
        <div className="bg-white px-3 py-2.5 space-y-2">
          {/* Location */}
          <div className="flex items-center gap-1.5 text-xs text-gray-700">
            <MapPin className="h-3.5 w-3.5 text-purple-600 flex-shrink-0" />
            <span className="font-semibold">{blockface.streetName}</span>
            <span className="text-gray-500">({blockface.side})</span>
          </div>

          {/* Rules */}
          {legalityResult.applicableRules.length > 0 && (
            <div>
              <h3 className="text-xs font-bold text-gray-700 mb-1">Rules:</h3>
              <ul className="space-y-0.5">
                {legalityResult.applicableRules.map((rule) => (
                  <li key={rule.id} className="text-xs text-gray-600 pl-3 relative">
                    <span className="absolute left-0 text-purple-600">•</span>
                    {rule.description}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Next Restriction */}
          {legalityResult.status === 'legal' && nextRestriction && (
            <div className="bg-amber-50 rounded-lg px-2 py-1.5 border border-amber-200 flex items-start gap-1.5">
              <AlertCircle className="h-3.5 w-3.5 text-amber-600 flex-shrink-0 mt-0.5" />
              <div className="text-xs text-amber-900">
                <span className="font-semibold">Next restriction:</span> {getDayName(nextRestriction.date)} {format(nextRestriction.date, 'h:mm a')}
              </div>
            </div>
          )}

          {/* Footer */}
          <div className="flex items-center justify-between pt-1.5 border-t border-gray-100">
            <div className="flex items-center gap-1 text-xs text-gray-500">
              <Clock className="h-3 w-3" />
              <span>{format(new Date(), 'MMM d')}</span>
            </div>
            
            <Button
              onClick={onReportError}
              variant="ghost"
              size="sm"
              className="text-xs text-purple-600 hover:text-purple-700 hover:bg-purple-50 rounded-full h-6 px-2 -mr-1"
            >
              Report
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}