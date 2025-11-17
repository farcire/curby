import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Calendar } from '@/components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Clock, Calendar as CalendarIcon, Zap } from 'lucide-react';
import { format, addDays, isAfter, startOfDay } from 'date-fns';

interface TimeControlsProps {
  selectedTime: Date;
  durationMinutes: number;
  onTimeChange: (time: Date) => void;
  onDurationChange: (minutes: number) => void;
}

const DURATION_OPTIONS = [
  { value: 60, label: '1 hour', emoji: '☕' },
  { value: 120, label: '2 hours', emoji: '🍽️' },
  { value: 180, label: '3 hours', emoji: '🛍️' },
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
  const selectedDuration = DURATION_OPTIONS.find(opt => opt.value === durationMinutes);

  return (
    <div className="bg-white border-b-2 border-purple-100 p-4 space-y-3 shadow-sm">
      <div className="flex items-center justify-between">
        <h2 className="text-base font-bold text-gray-900 flex items-center gap-2">
          <span className="text-xl">🕐</span>
          When do you need parking?
        </h2>
        <Button
          variant="outline"
          size="sm"
          onClick={handleNowClick}
          className="text-xs rounded-full border-2 border-purple-200 hover:bg-purple-50 hover:border-purple-300 transition-all"
        >
          <Zap className="h-3 w-3 mr-1" />
          Right Now!
        </Button>
      </div>

      <div className="grid grid-cols-2 gap-3">
        {/* Date Picker */}
        <div className="space-y-2">
          <Label className="text-xs text-gray-600 font-semibold flex items-center gap-1">
            <span>📅</span>
            Day
          </Label>
          <Popover open={isCalendarOpen} onOpenChange={setIsCalendarOpen}>
            <PopoverTrigger asChild>
              <Button
                variant="outline"
                className="w-full justify-start text-left font-normal rounded-xl border-2 hover:border-purple-300 hover:bg-purple-50 transition-all"
              >
                <CalendarIcon className="mr-2 h-4 w-4 text-purple-600" />
                <span className="text-sm font-medium">
                  {isToday ? '✨ Today' : format(selectedTime, 'MMM d')}
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
        <div className="space-y-2">
          <Label className="text-xs text-gray-600 font-semibold flex items-center gap-1">
            <span>⏰</span>
            Time
          </Label>
          <Select value={selectedTimeStr} onValueChange={handleTimeChange}>
            <SelectTrigger className="rounded-xl border-2 hover:border-purple-300 hover:bg-purple-50 transition-all">
              <Clock className="mr-2 h-4 w-4 text-purple-600" />
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
      <div className="space-y-2">
        <Label className="text-xs text-gray-600 font-semibold flex items-center gap-1">
          <span>⏱️</span>
          How long will you be?
        </Label>
        <Select 
          value={durationMinutes.toString()} 
          onValueChange={(val) => onDurationChange(parseInt(val))}
        >
          <SelectTrigger className="rounded-xl border-2 hover:border-purple-300 hover:bg-purple-50 transition-all">
            <div className="flex items-center gap-2">
              <span className="text-lg">{selectedDuration?.emoji}</span>
              <SelectValue />
            </div>
          </SelectTrigger>
          <SelectContent>
            {DURATION_OPTIONS.map((option) => (
              <SelectItem key={option.value} value={option.value.toString()}>
                <div className="flex items-center gap-2">
                  <span>{option.emoji}</span>
                  <span>{option.label}</span>
                </div>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="text-xs text-gray-600 bg-gradient-to-r from-blue-50 to-purple-50 p-3 rounded-xl border border-purple-100 flex items-center gap-2">
        <span className="text-base">🔍</span>
        <span>
          Looking for parking on <strong>{format(selectedTime, 'MMM d')}</strong> at <strong>{format(selectedTime, 'h:mm a')}</strong> for <strong>{durationMinutes / 60}hr</strong>
        </span>
      </div>
    </div>
  );
}