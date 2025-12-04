import { Blockface, LegalityResult } from '@/types/parking';
import { format, addDays, getDay } from 'date-fns';
import { X, Clock, MapPin, AlertCircle, Navigation } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { formatRulesForDisplay } from '@/utils/ruleFormatter';

interface BlockfaceDetailProps {
  blockface: Blockface;
  legalityResult: LegalityResult;
  onReportError: () => void;
  onClose: () => void;
}

// Helper function to remove leading zeros from street names
function cleanStreetName(street: string | undefined): string {
  if (!street) return '';
  // Remove leading zeros from street numbers (e.g., "02nd St" -> "2nd St")
  return street.replace(/\b0+(\d)/g, '$1');
}

export function BlockfaceDetail({ blockface, legalityResult, onReportError, onClose }: BlockfaceDetailProps) {
  const getStatusConfig = () => {
    switch (legalityResult.status) {
      case 'legal':
        return {
          gradient: 'from-green-500 to-emerald-600',
          emoji: '✅',
          text: 'You can park here!'
        };
      case 'illegal':
        return {
          gradient: 'from-red-500 to-rose-600',
          emoji: '🚫',
          text: "Don't park here!"
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

  // Check if permit is required
  const hasPermitRequirement = blockface.rules.some(rule => rule.type === 'rpp-zone');

  const status = getStatusConfig();

  // Format rules for display
  const formattedRules = formatRulesForDisplay(blockface.rules);

  return (
    <div className="fixed inset-x-0 bottom-0 z-50 flex justify-center p-3 pointer-events-none">
      <div className="w-full max-w-sm pointer-events-auto animate-in slide-in-from-bottom-4 duration-300 shadow-2xl rounded-xl overflow-hidden max-h-[80vh] flex flex-col">
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

        {/* Content - Scrollable */}
        <div className="bg-white px-4 py-3 space-y-3 overflow-y-auto flex-1">
          {/* Location */}
          <div className="flex items-center gap-2 text-sm text-gray-700">
            <MapPin className="h-4 w-4 text-purple-600 flex-shrink-0" />
            <span className="font-semibold">{cleanStreetName(blockface.streetName)}</span>
            <span className="text-gray-500">
              ({blockface.cardinalDirection || blockface.side}
              {blockface.fromAddress && blockface.toAddress ? `, ${blockface.fromAddress}-${blockface.toAddress}` : ''})
            </span>
          </div>
          
          {/* Limits (if available) */}
          {(blockface.fromStreet || blockface.toStreet) && (
            <div className="text-sm text-gray-500 flex items-center gap-1">
              {blockface.fromStreet && blockface.toStreet
                ? `${cleanStreetName(blockface.fromStreet)} → ${cleanStreetName(blockface.toStreet)}`
                : cleanStreetName(blockface.fromStreet || blockface.toStreet)}
            </div>
          )}

          {/* All Rules - Formatted and merged */}
          <div>
            <h3 className="text-xs font-bold text-gray-700 mb-1 uppercase">Rules:</h3>
            {formattedRules.length > 0 ? (
              <ul className="space-y-1">
                {formattedRules.map((ruleText, idx) => (
                  <li key={idx} className="text-sm text-gray-600 pl-3 relative">
                    <span className="absolute left-0 text-purple-600">•</span>
                    {ruleText}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-gray-600">No parking rules available</p>
            )}
          </div>

          {/* Next Restriction - Day and Time only */}
          {legalityResult.status === 'legal' && nextRestriction && (
            <div className="bg-amber-50 rounded-lg p-2 border border-amber-200 flex items-start gap-2">
              <AlertCircle className="h-4 w-4 text-amber-600 flex-shrink-0 mt-0.5" />
              <div className="text-sm text-amber-900">
                <span className="font-semibold">Next restriction:</span> {getDayName(nextRestriction.date)} {format(nextRestriction.date, 'h:mma')}
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center justify-between pt-2 border-t border-gray-100">
            <button
              onClick={onReportError}
              className="text-xs text-purple-600 hover:text-purple-700 font-medium"
            >
              Report Error
            </button>
            <button
              onClick={() => {
                const coords = blockface.geometry.coordinates;
                const lat = coords[0][1];
                const lng = coords[0][0];
                const url = `https://maps.google.com/?q=${lat},${lng}`;
                window.open(url, '_blank');
              }}
              className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-700 font-medium"
            >
              <Navigation className="h-3 w-3" />
              Get Directions
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}