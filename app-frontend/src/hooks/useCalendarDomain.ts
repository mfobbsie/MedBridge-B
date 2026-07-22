import { useMemo } from 'react';
import { useRemindersDomain } from './useRemindersDomain';


export interface CalendarEvent {
  id: string;
  title: string;
  start: Date;
  end: Date;
  type: 'medication' | 'appointment' | 'other';
  notes: string;
  completed: boolean;
}

export interface SaveEventParams {
  isEditing: boolean;
  editingEventId: string | null;
  title: string;
  type: 'medication' | 'appointment' | 'other';
  notes: string;
  startDate: string;
  startTime: string;
  endDate: string;
  endTime: string;
}

export const formatReminderBody = (notes: string, endCombinedIso: string): string => {
  const trimmedNotes = notes.trim();
  return trimmedNotes
    ? `${trimmedNotes} \n\n__END_TIME__:${endCombinedIso}`
    : `__END_TIME__:${endCombinedIso}`;
};

export const mapReminderToCalendarEvent = (rem: any): CalendarEvent => {
  const reminderStart = new Date(rem.remind_at);
  let reminderEnd = new Date(reminderStart.getTime() + 60 * 60 * 1000); // 1-hour fallback
  let notes = rem.body || '';

  if (rem.body && rem.body.includes('__END_TIME__:')) {
    try {
      const parts = rem.body.split('__END_TIME__:');
      notes = parts[0]?.trim() || '';
      const endIso = parts[1]?.trim();
      if (endIso) {
        const parsedEnd = new Date(endIso);
        if (!isNaN(parsedEnd.getTime())) {
          reminderEnd = parsedEnd;
        }
      }
    } catch (e) {
      console.error('Failed to parse end timestamp context', e);
    }
  }

  const normalizedType =
    rem.reminder_type === 'medication' || rem.reminder_type === 'appointment'
      ? rem.reminder_type
      : 'other';

  return {
    id: rem.id,
    title: rem.title,
    start: reminderStart,
    end: reminderEnd,
    type: normalizedType,
    notes,
    completed: rem.completed,
  };
};


export const useCalendarDomain = () => {
  const { data, flags, actions } = useRemindersDomain();

  // Transform backend list into CalendarEvent objects using the Rule layer
  const events: CalendarEvent[] = useMemo(() => {
    return data.remindersList.map(mapReminderToCalendarEvent);
  }, [data.remindersList]);

  const saveEvent = (params: SaveEventParams) => {
    const { 
      isEditing, 
      editingEventId, 
      title, 
      type, 
      notes, 
      startDate, 
      startTime, 
      endDate, 
      endTime 
    } = params;

    if (!title?.trim()) return;

    const startCombined = new Date(`${startDate}T${startTime}`).toISOString();
    const endCombined = new Date(`${endDate}T${endTime}`).toISOString();
    
    // Format the payload using the Rule layer
    const bodyPayload = formatReminderBody(notes || '', endCombined);

    const payload = {
      reminder_type: type,
      title: title.trim(),
      body: bodyPayload,
      remind_at: startCombined,
      repeat_interval: null,
    };

    if (isEditing && editingEventId) {
      actions.modifyReminder(editingEventId, payload);
    } else {
      actions.scheduleReminder(payload);
    }
  };

  const deleteEvent = (id: string | null) => {
    if (id) actions.removeReminder(id);
  };

  const completeEvent = (id: string | null) => {
    if (id) actions.markAsComplete(id);
  };

  return {
    events,
    isLoading: flags.isPending,
    hasError: flags.hasError,
    errorMessage: flags.errorMessage,
    isActionInFlight: flags.isActionInFlight,
    saveEvent,
    deleteEvent,
    completeEvent,
  };
};