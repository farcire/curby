import { useState } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Blockface, ErrorReport } from '@/types/parking';
import { showSuccess } from '@/utils/toast';

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

    // Create error report
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

    // Save to localStorage (demo purposes)
    const existingReports = JSON.parse(localStorage.getItem('curby-error-reports') || '[]');
    existingReports.push(report);
    localStorage.setItem('curby-error-reports', JSON.stringify(existingReports));

    showSuccess('Error report submitted! Thank you for helping improve Curby.');
    
    setDescription('');
    setIsSubmitting(false);
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Report Incorrect Rule</DialogTitle>
          <DialogDescription>
            Help us improve parking data accuracy. Describe what's incorrect about the parking rules for this location.
          </DialogDescription>
        </DialogHeader>

        {blockface && (
          <div className="py-4 space-y-4">
            <div className="text-sm">
              <p className="font-medium text-gray-900">{blockface.streetName}</p>
              <p className="text-gray-600 capitalize">{blockface.side} side</p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">What's incorrect?</Label>
              <Textarea
                id="description"
                placeholder="Example: The street sweeping time is wrong - it's actually Wednesday 10am-12pm, not Tuesday..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={4}
                className="resize-none"
              />
            </div>
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button 
            onClick={handleSubmit} 
            disabled={!description.trim() || isSubmitting}
          >
            {isSubmitting ? 'Submitting...' : 'Submit Report'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}