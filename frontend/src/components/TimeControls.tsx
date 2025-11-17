import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Calendar } from '@/components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Clock, Calendar as CalendarIcon } from 'lucide-react';
import { format, addDays, isAfter, startOfDay } from 'date-fns';

interface TimeControlsProps {
  selectedTime: Date;
  durationMinutes: number;
  onTimeChange: (time: Date) => void;
  onDurationChange: (minutes: number) => void;
}

const DURATION_OPTIONS = [
  { value: 15, label: '15 min' },
  { value: 30, label: '30 min' },
  { value: 60, label: '1 hour' },
  { value: 90, label: '1.5 hours' },
  { value: 120, label: '2 hours' },
  { value: 180, label: '3 hours' },
  { value: 240, label: '4 hours' },
];

const TIME_OPTIONS = Array.from({ length: 24 }, (_, i) => {
  const hour = i.toString().padStart(2, '0');
  return [
    { value: `${hour}:00`, label: `${i === 0 ? 12 : i > 12 ? i - 12 : i}:00 ${i < 12 ? 'AM' : 'PM'}` },
    { value: `${hour}:30`, label: `${i === 0 ? 12 : i > 12 ? i - 12 : i}:30 ${i < 12 ? 'AM' : 'PM'}` },
  ];
}).flat();

export function TimeControls({ selectedTime, durationMinutes, onTimeChange, onDurationChange }: TimeControlsProps) {
  const [isCalendarOpen, setIsCalendarOpen] = useState(false);
  
  const maxDate = addDays(new Date(), 7);
  const selectedDate = startOfDay(selectedTime);
  const selectedTimeStr = format(selectedTime, 'HH:mm');

  const handleDateChange = (date: Date | undefined) => {
    if (!date) return;
    
    // Combine selected date with current time
    const [hours, minutes] = selectedTimeStr.split(':').map(Number);
    const newDateTime = new Date(date);
    newDateTime.setHours(hours, minutes, 0, 0);
    
    onTimeChange(newDateTime);
    setIsCalendarOpen(false);
  };

  const handleTimeChange = (timeStr: string) => {
    const [hours, minutes] = timeStr.split(':').map(Number);
    const newDateTime = new Date(selectedTime);
    newDateTime.setHours(hours, minutes, 0, 0);
    onTimeChange(newDateTime);
  };

  const handleNowClick = () => {
    onTimeChange(new Date());
  };

  const isToday = format(selectedTime, 'yyyy-MM-dd') === format(new Date(), 'yyyy-MM-dd');

  return (
    <div className="bg-white border-b border-gray-200 p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-gray-900">Check Parking Legality</h2>
        <Button
          variant="outline"
          size="sm"
          onClick={handleNowClick}
          className="text-xs"
        >
          Now
        </Button>
      </div>

      <div className="grid grid-cols-2 gap-3">
        {/* Date Picker */}
        <div className="space-y-1.5">
          <Label className="text-xs text-gray-600">Date</Label>
          <Popover open={isCalendarOpen} onOpenChange={setIsCalendarOpen}>
            <PopoverTrigger asChild>
              <Button
                variant="outline"
                className="w-full justify-start text-left font-normal"
              >
                <CalendarIcon className="mr-2 h-4 w-4" />
                <span className="text-sm">
                  {isToday ? 'Today' : format(selectedTime, 'MMM d')}
                </span>
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-0" align="start">
              <Calendar
                mode="single"
                selected={selectedDate}
                onSelect={handleDateChange}
                disabled={(date) => 
                  date < startOfDay(new Date()) || 
                  isAfter(date, maxDate)
                }
                initialFocus
              />
            </PopoverContent>
          </Popover>
        </div>

        {/* Time Picker */}
        <div className="space-y-1.5">
          <Label className="text-xs text-gray-600">Time</Label>
          <Select value={selectedTimeStr} onValueChange={handleTimeChange}>
            <SelectTrigger>
              <Clock className="mr-2 h-4 w-4" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="max-h-[300px]">
              {TIME_OPTIONS.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Duration Selector */}
      <div className="space-y-1.5">
        <Label className="text-xs text-gray-600">Parking Duration</Label>
        <Select 
          value={durationMinutes.toString()} 
          onValueChange={(val) => onDurationChange(parseInt(val))}
        >
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {DURATION_OPTIONS.map((option) => (
              <SelectItem key={option.value} value={option.value.toString()}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="text-xs text-gray-500 bg-blue-50 p-2 rounded">
        ℹ️ Checking legality for {format(selectedTime, 'MMM d, h:mm a')} ({durationMinutes / 60}hr duration)
      </div>
    </div>
  );
}