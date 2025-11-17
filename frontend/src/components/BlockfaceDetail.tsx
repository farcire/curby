import { Blockface, LegalityResult } from '@/types/parking';
import { format } from 'date-fns';

interface BlockfaceDetailProps {
  blockface: Blockface;
  legalityResult: LegalityResult;
  onReportError: () => void;
  onClose: () => void;
}

export function BlockfaceDetail({ blockface, legalityResult, onReportError, onClose }: BlockfaceDetailProps) {
  const getStatusIndicator = () => {
    switch (legalityResult.status) {
      case 'legal':
        return { color: 'text-green-400', dot: '●', text: 'LEGAL TO PARK HERE' };
      case 'illegal':
        return { color: 'text-red-400', dot: '●', text: 'DO NOT PARK HERE' };
      case 'insufficient-data':
        return { color: 'text-gray-400', dot: '●', text: 'INSUFFICIENT DATA' };
    }
  };

  const status = getStatusIndicator();

  // Get explanation icon
  const getExplanationIcon = () => {
    switch (legalityResult.status) {
      case 'legal':
        return '✅';
      case 'illegal':
        return '❌';
      case 'insufficient-data':
        return '❓';
    }
  };

  return (
    <div className="fixed inset-x-0 bottom-0 z-50 bg-gray-900 text-gray-100 border-t-2 border-gray-700 max-h-[70vh] overflow-y-auto font-mono animate-in slide-in-from-bottom-4 duration-300">
      {/* Close button */}
      <button 
        onClick={onClose}
        className="absolute top-4 right-4 text-gray-500 hover:text-gray-300 text-xl font-bold"
      >
        ✕
      </button>

      <div className="p-6 space-y-6">
        {/* Status Header */}
        <div className="space-y-3">
          <div className={`flex items-center gap-2 text-lg font-bold ${status.color}`}>
            <span>{status.dot}</span>
            <span>{status.text}</span>
          </div>

          {/* Location */}
          <div className="flex items-start gap-2 text-sm text-gray-400">
            <span className="text-red-400">📍</span>
            <span className="capitalize">
              {blockface.streetName} ({blockface.side} side)
            </span>
          </div>
        </div>

        {/* Explanation - Always show this prominently */}
        {legalityResult.explanation && (
          <div className="flex items-start gap-3 text-base text-gray-300 bg-gray-800/50 p-4 rounded border border-gray-700">
            <span className="text-xl flex-shrink-0">{getExplanationIcon()}</span>
            <span>{legalityResult.explanation}</span>
          </div>
        )}

        {/* Rules Section - Only show if there are applicable rules */}
        {legalityResult.applicableRules.length > 0 && (
          <div className="space-y-2 pt-2 border-t border-gray-800">
            <div className="text-sm font-bold text-gray-300">RULES:</div>
            <ul className="space-y-1 text-sm text-gray-400">
              {legalityResult.applicableRules.map((rule) => (
                <li key={rule.id} className="flex items-start gap-2">
                  <span>•</span>
                  <span>{rule.description}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Next Restriction Warning - Only show for legal spots with rules */}
        {legalityResult.status === 'legal' && legalityResult.applicableRules.length > 0 && (
          <div className="space-y-2 pt-2 border-t border-gray-800">
            <div className="flex items-center gap-2 text-sm text-amber-400">
              <span>⚠️</span>
              <span className="font-bold">NEXT RESTRICTION:</span>
            </div>
            <div className="text-sm text-gray-400 pl-6">
              Check signs for time limits and restrictions
            </div>
          </div>
        )}

        {/* Warnings */}
        {legalityResult.warnings && legalityResult.warnings.length > 0 && (
          <div className="space-y-1 text-xs text-gray-500 pt-2 border-t border-gray-800">
            {legalityResult.warnings.map((warning, idx) => (
              <div key={idx}>• {warning}</div>
            ))}
          </div>
        )}

        {/* Footer */}
        <div className="space-y-3 pt-4 border-t border-gray-800">
          <div className="text-xs text-gray-600">
            Data updated: {format(new Date(), 'MMM d, yyyy')}
          </div>
          
          <button
            onClick={onReportError}
            className="text-sm text-gray-500 hover:text-gray-300 underline"
          >
            [Report incorrect info]
          </button>
        </div>
      </div>
    </div>
  );
}