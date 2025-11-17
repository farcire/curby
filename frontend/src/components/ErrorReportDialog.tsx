import { useState } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Blockface, ErrorReport } from '@/types/parking';
import { showSuccess } from '@/utils/toast';
import { Heart, Send } from 'lucide-react';

interface ErrorReportDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  blockface: Blockface | null;
}

export function ErrorReportDialog({ open, onOpenChange, blockface }: ErrorReportDialogProps) {
  const [description, setDescription] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = () => {
    if (!blockface || !description.trim()) return;

    setIsSubmitting(true);

    const report: ErrorReport = {
      id: `report-${Date.now()}`,
      blockfaceId: blockface.id,
      location: {
        lat: blockface.geometry.coordinates[0][1],
        lng: blockface.geometry.coordinates[0][0],
      },
      description: description.trim(),
      timestamp: new Date().toISOString(),
    };

    const existingReports = JSON.parse(localStorage.getItem('curby-error-reports') || '[]');
    existingReports.push(report);
    localStorage.setItem('curby-error-reports', JSON.stringify(existingReports));

    showSuccess('🎉 Thanks for helping make Curby better!');
    
    setDescription('');
    setIsSubmitting(false);
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px] rounded-2xl">
        <DialogHeader>
          <DialogTitle className="text-xl flex items-center gap-2">
            <span className="text-2xl">🤝</span>
            Help Us Get It Right
          </DialogTitle>
          <DialogDescription className="text-sm text-gray-600 leading-relaxed">
            Spotted something off? We'd love to know! Your feedback helps everyone find parking more easily.
          </DialogDescription>
        </DialogHeader>

        {blockface && (
          <div className="py-4 space-y-4">
            <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-xl p-4 border-2 border-purple-200">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xl">📍</span>
                <p className="font-semibold text-gray-900">{blockface.streetName}</p>
              </div>
              <p className="text-sm text-gray-600 capitalize ml-7">{blockface.side} side</p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="description" className="text-sm font-semibold text-gray-900">
                What's not quite right?
              </Label>
              <Textarea
                id="description"
                placeholder="For example: 'The street sweeping is actually on Wednesday mornings, not Tuesday' or 'There's a new 2-hour limit sign here now'"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={4}
                className="resize-none rounded-xl border-2 focus:border-purple-300"
              />
              <p className="text-xs text-gray-500 flex items-center gap-1">
                💡 The more details, the better we can help!
              </p>
            </div>
          </div>
        )}

        <DialogFooter className="gap-2">
          <Button 
            variant="outline" 
            onClick={() => onOpenChange(false)}
            className="rounded-xl"
          >
            Maybe Later
          </Button>
          <Button 
            onClick={handleSubmit} 
            disabled={!description.trim() || isSubmitting}
            className="rounded-xl bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700"
          >
            {isSubmitting ? (
              <>
                <Heart className="mr-2 h-4 w-4 animate-pulse" />
                Sending...
              </>
            ) : (
              <>
                <Send className="mr-2 h-4 w-4" />
                Send Feedback
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}