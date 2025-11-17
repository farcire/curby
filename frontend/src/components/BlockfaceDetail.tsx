import { Blockface, LegalityResult } from '@/types/parking';
import { format, addDays, getDay, differenceInHours, differenceInMinutes } from 'date-fns';
import { X, AlertTriangle, CheckCircle, HelpCircle, Clock } from 'lucide-react';
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
          icon: <CheckCircle className="h-8 w-8" />,
          emoji: '✅',
          text: 'You can park here!'
        };
      case 'illegal':
        return { 
          gradient: 'from-red-500 to-rose-600',
          icon: <X className="h-8 w-8" />,
          emoji: '🚫',
          text: "Don't park here!"
        };
      case 'insufficient-data':
        return { 
          gradient: 'from-gray-500 to-slate-600',
          icon: <HelpCircle className="h-8 w-8" />,
          emoji: '🤔',
          text: 'Not sure about this spot'
        };
    }
  };

  // Calculate next restriction
  const getNextRestriction = () => {
    const now = new Date();
    const currentDay = getDay(now);
    
    // Find all future restrictions
    const upcomingRestrictions = blockface.rules
      .filter(rule => rule.type === 'street-sweeping' || rule.type === 'no-parking' || rule.type === 'tow-away')
      .flatMap(rule => {
        return rule.timeRanges.map(range => {
          // Find next occurrence of each day
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
      return `in ${days} ${days === 1 ? 'day' : 'days'}`;
    }
  };

  const getDayName = (date: Date) => {
    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    return days[getDay(date)];
  };

  const status = getStatusConfig();

  return (
    <div className="fixed inset-x-0 bottom-0 z-50 max-h-[80vh] overflow-y-auto animate-in slide-in-from-bottom-4 duration-300">
      {/* Status Header */}
      <div className={`bg-gradient-to-r ${status.gradient} text-white p-6 shadow-2xl relative overflow-hidden`}>
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-0 left-0 w-32 h-32 bg-white rounded-full -translate-x-16 -translate-y-16"></div>
          <div className="absolute bottom-0 right-0 w-40 h-40 bg-white rounded-full translate-x-20 translate-y-20"></div>
        </div>

        <button 
          onClick={onClose}
          className="absolute top-4 right-4 text-white/80 hover:text-white bg-white/20 hover:bg-white/30 rounded-full p-2 transition-all"
        >
          <X className="h-5 w-5" />
        </button>

        <div className="relative space-y-3">
          <div className="flex items-center gap-3">
            <span className="text-4xl">{status.emoji}</span>
            <div>
              <h2 className="text-2xl font-bold">{status.text}</h2>
              <p className="text-sm text-white/90 capitalize">
                📍 {blockface.streetName} ({blockface.side} side)
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="bg-gradient-to-br from-purple-50 via-pink-50 to-orange-50 p-6 space-y-4">
        {/* Explanation Card */}
        <div className="bg-white rounded-2xl p-4 shadow-lg border-2 border-purple-200">
          <div className="flex items-start gap-3">
            <span className="text-2xl flex-shrink-0">💬</span>
            <p className="text-gray-900 font-medium leading-relaxed">
              {legalityResult.explanation}
            </p>
          </div>
        </div>

        {/* Next Restriction - Only show for legal spots */}
        {legalityResult.status === 'legal' && nextRestriction && (
          <div className="bg-gradient-to-br from-amber-100 to-orange-100 rounded-2xl p-4 shadow-lg border-2 border-amber-300">
            <div className="flex items-start gap-3 mb-3">
              <AlertTriangle className="h-6 w-6 text-amber-700 flex-shrink-0 mt-1" />
              <div className="flex-1">
                <h3 className="text-lg font-bold text-amber-900 mb-1">⏰ Next Restriction</h3>
                <p className="text-sm text-amber-800">
                  <strong>{getDayName(nextRestriction.date)}</strong> at{' '}
                  <strong>{format(nextRestriction.date, 'h:mm a')}</strong>
                  {' '}({formatTimeUntil(nextRestriction.date)})
                </p>
              </div>
            </div>
            <div className="bg-white/60 rounded-xl p-3 border border-amber-200">
              <p className="text-sm text-amber-900 font-medium">
                🧹 {nextRestriction.rule.description}
              </p>
            </div>
          </div>
        )}

        {/* Rules Section */}
        {legalityResult.applicableRules.length > 0 && (
          <div className="bg-white rounded-2xl p-4 shadow-lg border-2 border-purple-200">
            <h3 className="text-sm font-bold text-gray-900 mb-3 flex items-center gap-2">
              <span className="text-lg">📋</span>
              Parking Rules
            </h3>
            <ul className="space-y-2">
              {legalityResult.applicableRules.map((rule) => (
                <li key={rule.id} className="flex items-start gap-2 text-sm text-gray-700">
                  <span className="text-purple-600 font-bold">•</span>
                  <span>{rule.description}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Warnings */}
        {legalityResult.warnings && legalityResult.warnings.length > 0 && (
          <div className="bg-blue-50 rounded-2xl p-4 border-2 border-blue-200">
            <div className="flex items-start gap-2">
              <span className="text-lg">💡</span>
              <div className="space-y-1 text-xs text-blue-900">
                {legalityResult.warnings.map((warning, idx) => (
                  <p key={idx}>{warning}</p>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="flex items-center justify-between pt-2">
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <Clock className="h-3 w-3" />
            <span>Updated {format(new Date(), 'MMM d, yyyy')}</span>
          </div>
          
          <Button
            onClick={onReportError}
            variant="ghost"
            size="sm"
            className="text-xs text-purple-600 hover:text-purple-700 hover:bg-purple-50 rounded-full"
          >
            🐛 Report Issue
          </Button>
        </div>
      </div>
    </div>
  );
}