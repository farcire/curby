import { Blockface, LegalityResult } from '@/types/parking';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { AlertTriangle, CheckCircle, XCircle, HelpCircle, Flag } from 'lucide-react';
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
        return <CheckCircle className="h-6 w-6 text-green-600" />;
      case 'limited':
        return <AlertTriangle className="h-6 w-6 text-amber-600" />;
      case 'illegal':
        return <XCircle className="h-6 w-6 text-red-600" />;
      case 'insufficient-data':
        return <HelpCircle className="h-6 w-6 text-gray-600" />;
    }
  };

  const getStatusLabel = () => {
    switch (legalityResult.status) {
      case 'legal':
        return 'Legal to Park';
      case 'limited':
        return 'Limited Parking';
      case 'illegal':
        return 'Illegal to Park';
      case 'insufficient-data':
        return 'Insufficient Data';
    }
  };

  return (
    <div className="fixed inset-x-0 bottom-0 z-50 bg-white rounded-t-2xl shadow-2xl max-h-[70vh] overflow-y-auto">
      <div className="sticky top-0 bg-white border-b border-gray-200 p-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          {getStatusIcon()}
          <div>
            <h3 className="font-semibold text-gray-900">{blockface.streetName}</h3>
            <p className="text-sm text-gray-600 capitalize">{blockface.side} side</p>
          </div>
        </div>
        <Button variant="ghost" size="sm" onClick={onClose}>
          ✕
        </Button>
      </div>

      <div className="p-4 space-y-4">
        {/* Status Badge */}
        <Card 
          className="p-4"
          style={{ 
            borderLeft: `4px solid ${getStatusColor(legalityResult.status)}`,
          }}
        >
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-lg">{getStatusLabel()}</span>
            </div>
            <p className="text-sm text-gray-700 leading-relaxed">
              {legalityResult.explanation}
            </p>
          </div>
        </Card>

        {/* Warnings */}
        {legalityResult.warnings && legalityResult.warnings.length > 0 && (
          <Card className="p-4 bg-amber-50 border-amber-200">
            <h4 className="font-medium text-sm text-amber-900 mb-2">Important Notes:</h4>
            <ul className="space-y-1">
              {legalityResult.warnings.map((warning, idx) => (
                <li key={idx} className="text-xs text-amber-800 flex items-start gap-2">
                  <span className="mt-0.5">•</span>
                  <span>{warning}</span>
                </li>
              ))}
            </ul>
          </Card>
        )}

        {/* All Applicable Rules */}
        {legalityResult.applicableRules.length > 0 && (
          <div className="space-y-2">
            <h4 className="font-medium text-sm text-gray-900">Parking Rules:</h4>
            <div className="space-y-2">
              {legalityResult.applicableRules.map((rule) => (
                <Card key={rule.id} className="p-3 bg-gray-50">
                  <p className="text-xs text-gray-700">{rule.description}</p>
                  {rule.metadata && (
                    <div className="mt-1 text-xs text-gray-500">
                      {rule.metadata.meterRate && (
                        <span>Rate: ${rule.metadata.meterRate}/hr</span>
                      )}
                      {rule.metadata.timeLimit && (
                        <span>Limit: {rule.metadata.timeLimit / 60} hours</span>
                      )}
                      {rule.metadata.permitZone && (
                        <span>Zone: {rule.metadata.permitZone}</span>
                      )}
                    </div>
                  )}
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* Report Error Button */}
        <Button
          variant="outline"
          className="w-full"
          onClick={onReportError}
        >
          <Flag className="mr-2 h-4 w-4" />
          Report Incorrect Rule
        </Button>

        <p className="text-xs text-center text-gray-500">
          This is a prototype with mock data for Mission + SOMA neighborhoods
        </p>
      </div>
    </div>
  );
}