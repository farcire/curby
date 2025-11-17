import { Blockface, LegalityResult } from '@/types/parking';
import { format, addDays, getDay, differenceInHours, differenceInMinutes } from 'date-fns';
import { X, Clock, MapPin } from 'lucide-react';
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
          text: 'Legal to park here'
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
          text: 'Insufficient data'
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

  const formatTimeUntil = (date: Date) => {
    const now = new Date();
    const hours = differenceInHours(date, now);
    const minutes = differenceInMinutes(date, now) % 60;

    if (hours < 24) {
      return `in ${hours}h ${minutes}m`;
    } else {
      const days = Math.floor(hours / 24);
      return `in ${days}d`;
    }
  };

  const getDayName = (date: Date) => {
    const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    return days[getDay(date)];
  };

  const status = getStatusConfig();

  return (
    <div className="fixed inset-x-0 bottom-0 z-50 animate-in slide-in-from-bottom-4 duration-300 shadow-2xl">
      {/* Compact Header */}
      <div className={`bg-gradient-to-r ${status.gradient} text-white px-4 py-2 flex items-center justify-between`}>
        <div className="flex items-center gap-2">
          <span className="text-xl">{status.emoji}</span>
          <div>
            <h2 className="text-sm font-bold">{status.text}</h2>
            <p className="text-xs text-white/90 flex items-center gap-1">
              <MapPin className="h-3 w-3" />
              {blockface.streetName} ({blockface.side} side)
            </p>
          </div>
        </div>
        <button 
          onClick={onClose}
          className="text-white/80 hover:text-white bg-white/20 hover:bg-white/30 rounded-full p-1 transition-all"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* Compact Content */}
      <div className="bg-white px-4 py-3 space-y-2">
        {/* Rules */}
        {legalityResult.applicableRules.length > 0 && (
          <div>
            <h3 className="text-xs font-bold text-gray-700 mb-1">Rules:</h3>
            <ul className="space-y-0.5">
              {legalityResult.applicableRules.map((rule) => (
                <li key={rule.id} className="text-xs text-gray-600 flex items-start gap-1">
                  <span className="text-purple-600 mt-0.5">•</span>
                  <span>{rule.description}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Next Restriction */}
        {legalityResult.status === 'legal' && nextRestriction && (
          <div className="bg-amber-50 rounded-lg px-2 py-1.5 border border-amber-200">
            <p className="text-xs text-amber-900">
              <strong>Next restriction:</strong> {getDayName(nextRestriction.date)} {format(nextRestriction.date, 'h:mm a')} ({formatTimeUntil(nextRestriction.date)})
            </p>
          </div>
        )}

        {/* Footer */}
        <div className="flex items-center justify-between pt-1 border-t border-gray-100">
          <div className="flex items-center gap-1 text-xs text-gray-500">
            <Clock className="h-3 w-3" />
            <span>Updated {format(new Date(), 'MMM d, yyyy')}</span>
          </div>
          
          <Button
            onClick={onReportError}
            variant="ghost"
            size="sm"
            className="text-xs text-purple-600 hover:text-purple-700 hover:bg-purple-50 rounded-full h-6 px-2"
          >
            Report Issue
          </Button>
        </div>
      </div>
    </div>
  );
}