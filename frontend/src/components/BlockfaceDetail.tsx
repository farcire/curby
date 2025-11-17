import { Blockface, LegalityResult } from '@/types/parking';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { XCircle, HelpCircle, Flag, Sparkles, PartyPopper } from 'lucide-react';
import { getStatusColor } from '@/utils/ruleEngine';

interface BlockfaceDetailProps {
  blockface: Blockface;
  legalityResult: LegalityResult;
  onReportError: () => void;
  onClose: () => void;
}

export function BlockfaceDetail({ blockface, legalityResult, onReportError, onClose }: BlockfaceDetailProps) {
  const getStatusIcon = () => {
    switch (legalityResult.status) {
      case 'legal':
        return <PartyPopper className="h-8 w-8 text-green-600" />;
      case 'illegal':
        return <XCircle className="h-8 w-8 text-red-600" />;
      case 'insufficient-data':
        return <HelpCircle className="h-8 w-8 text-gray-600" />;
    }
  };

  const getStatusEmoji = () => {
    switch (legalityResult.status) {
      case 'legal':
        return '🎉';
      case 'illegal':
        return '🚫';
      case 'insufficient-data':
        return '🤔';
    }
  };

  const getStatusLabel = () => {
    switch (legalityResult.status) {
      case 'legal':
        return 'Perfect Spot!';
      case 'illegal':
        return 'Keep Looking';
      case 'insufficient-data':
        return 'No Data';
    }
  };

  const getStatusMessage = () => {
    switch (legalityResult.status) {
      case 'legal':
        return "You found a winner! This spot is all yours. 🌟";
      case 'illegal':
        return "Not this one! Let's find you something better.";
      case 'insufficient-data':
        return "We don't have data for this spot yet. Check the signs to be safe!";
    }
  };

  return (
    <div className="fixed inset-x-0 bottom-0 z-50 bg-white rounded-t-3xl shadow-2xl max-h-[75vh] overflow-y-auto animate-in slide-in-from-bottom-4 duration-300">
      {/* Colorful Header */}
      <div 
        className="sticky top-0 bg-gradient-to-r from-white via-white to-white border-b-2 p-5 flex items-center justify-between"
        style={{ 
          borderBottomColor: getStatusColor(legalityResult.status),
        }}
      >
        <div className="flex items-center gap-4">
          <div className="bg-gradient-to-br from-purple-100 to-pink-100 rounded-2xl p-3">
            {getStatusIcon()}
          </div>
          <div>
            <div className="flex items-center gap-2 mb-1">
              <h3 className="font-bold text-xl text-gray-900">{blockface.streetName}</h3>
              <span className="text-2xl">{getStatusEmoji()}</span>
            </div>
            <p className="text-sm text-gray-600 capitalize flex items-center gap-2">
              <span className="inline-block w-2 h-2 bg-gray-400 rounded-full"></span>
              {blockface.side} side
            </p>
          </div>
        </div>
        <Button 
          variant="ghost" 
          size="sm" 
          onClick={onClose}
          className="rounded-full hover:bg-gray-100"
        >
          ✕
        </Button>
      </div>

      <div className="p-5 space-y-4">
        {/* Status Card with Personality */}
        <Card 
          className="p-5 relative overflow-hidden"
          style={{ 
            borderLeft: `6px solid ${getStatusColor(legalityResult.status)}`,
          }}
        >
          <div className="absolute top-0 right-0 w-32 h-32 opacity-5">
            {legalityResult.status === 'legal' && <Sparkles className="w-full h-full" />}
          </div>
          <div className="space-y-3 relative">
            <div className="flex items-center gap-2">
              <span className="font-bold text-xl text-gray-900">{getStatusLabel()}</span>
            </div>
            <p className="text-base text-gray-700 leading-relaxed font-medium">
              {getStatusMessage()}
            </p>
            <div className="pt-3 border-t border-gray-100">
              <p className="text-sm text-gray-600 leading-relaxed">
                {legalityResult.explanation}
              </p>
            </div>
          </div>
        </Card>

        {/* Friendly Warnings */}
        {legalityResult.warnings && legalityResult.warnings.length > 0 && (
          <Card className="p-4 bg-gradient-to-br from-amber-50 to-orange-50 border-2 border-amber-200 rounded-2xl">
            <div className="flex items-start gap-3">
              <span className="text-2xl">💡</span>
              <div className="flex-1">
                <h4 className="font-semibold text-sm text-amber-900 mb-2">Heads up!</h4>
                <ul className="space-y-2">
                  {legalityResult.warnings.map((warning, idx) => (
                    <li key={idx} className="text-xs text-amber-800 flex items-start gap-2">
                      <span className="mt-0.5 text-amber-600">•</span>
                      <span>{warning}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </Card>
        )}

        {/* Parking Rules - More Visual */}
        {legalityResult.applicableRules.length > 0 && (
          <div className="space-y-3">
            <h4 className="font-semibold text-sm text-gray-900 flex items-center gap-2">
              <span>📋</span>
              The Details
            </h4>
            <div className="space-y-2">
              {legalityResult.applicableRules.map((rule) => (
                <Card key={rule.id} className="p-4 bg-gradient-to-br from-gray-50 to-slate-50 border border-gray-200 rounded-xl hover:shadow-md transition-shadow">
                  <div className="flex items-start gap-3">
                    <span className="text-xl">
                      {rule.type === 'street-sweeping' && '🧹'}
                      {rule.type === 'meter' && '🪙'}
                      {rule.type === 'time-limit' && '⏰'}
                      {rule.type === 'rpp-zone' && '🏠'}
                      {rule.type === 'no-parking' && '🚫'}
                      {rule.type === 'tow-away' && '🚛'}
                    </span>
                    <div className="flex-1">
                      <p className="text-sm text-gray-700 font-medium">{rule.description}</p>
                      {rule.metadata && (
                        <div className="mt-2 flex flex-wrap gap-2">
                          {rule.metadata.meterRate && (
                            <span className="inline-flex items-center gap-1 text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">
                              💵 ${rule.metadata.meterRate}/hr
                            </span>
                          )}
                          {rule.metadata.timeLimit && (
                            <span className="inline-flex items-center gap-1 text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
                              ⏱️ {rule.metadata.timeLimit / 60}hr limit
                            </span>
                          )}
                          {rule.metadata.permitZone && (
                            <span className="inline-flex items-center gap-1 text-xs bg-purple-100 text-purple-800 px-2 py-1 rounded-full">
                              🎫 Zone {rule.metadata.permitZone}
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* Friendly Report Button */}
        <Button
          variant="outline"
          className="w-full rounded-xl border-2 hover:bg-purple-50 hover:border-purple-300 transition-all"
          onClick={onReportError}
        >
          <Flag className="mr-2 h-4 w-4" />
          Something look wrong? Let us know!
        </Button>

        <div className="text-center pt-2">
          <p className="text-xs text-gray-500 flex items-center justify-center gap-2">
            <Sparkles className="h-3 w-3" />
            Made with care for SF drivers
            <Sparkles className="h-3 w-3" />
          </p>
        </div>
      </div>
    </div>
  );
}