import { useMemo, useState } from 'react';
import { Calendar, dateFnsLocalizer, Views, type View } from 'react-big-calendar';
import { format, parse, startOfWeek, getDay, addHours } from 'date-fns';
import { enUS } from 'date-fns/locale';
import 'react-big-calendar/lib/css/react-big-calendar.css';
import type { CalendarEvent, ReminderResponse } from '../types/features';
import { useModal } from '../context/ModalContext';
import { FormFactory } from './FormFactory';
import "./CalendarView.css";
import { useMedicationDomain } from '../hooks/useMedicationDomain';
import { useRemindersDomain } from '../hooks/useRemindersDomain';
import type { MedicationResponse } from '../types/medication';
import { DeleteConfirm } from './DeleteConfirm';
import { LoadingSpinner } from './LoadingSpinner';
import { ErrorState } from './ErrorState';

const locales = { 'en-US': enUS };
const localizer = dateFnsLocalizer({ format, parse, startOfWeek, getDay, locales });


export default function CalendarView() {

  const { data: reminders, flags: reminderFlags, actions: reminderActions } = useRemindersDomain()
  const { data: medication, flags: medicationFlags, actions: medicationActions } = useMedicationDomain()
  const { openModal, closeModal } = useModal();

  const isPending = reminderFlags.isPending || medicationFlags.isPending;
  const hasError = reminderFlags.hasError || medicationFlags.hasError;
  const errorMessage = reminderFlags.errorMessage || medicationFlags.errorMessage;
  const isActionInFlight = reminderFlags.isActionInFlight || medicationFlags.isActionInFlight;

  const parseDateTime = (dateStr?: string | null, timeStr?: string | null): Date => {
    if (!dateStr) return new Date();
    const time = timeStr && timeStr.trim() !== '' ? timeStr : '00:00';
    return new Date(`${dateStr}T${time}`);
  }

  const events: CalendarEvent[] = useMemo(() => {

    const medicationEvents = (medication.medicationList || []).map((med: MedicationResponse) => {
      const startDate = med.start_date;
      const endDate = med.end_date || startDate;
      const defaultStartTime = '08:00';
      const defaultEndTime = '09:00';

      return {
        id: med.id,
        title: med.name || "Medication",
        type: "medication" as const,
        start: parseDateTime(startDate, defaultStartTime),
        end: parseDateTime(endDate, defaultEndTime),
        notes: med.notes || "",
        completed: !med.is_active,
        raw: med,
      };
    });

    const reminderEvents = (reminders.remindersList || []).map((rem: ReminderResponse) => {
      const startDate = rem.remind_at ? new Date(rem.remind_at) : new Date();
      const endDate = new Date(startDate.getTime() + 60 * 60 * 1000);

      return {
        id: rem.id,
        title: rem.title || "Reminder",
        type: (rem.reminder_type || "appointment") as CalendarEvent["type"],
        start: startDate,
        end: endDate,
        notes: rem.body || "",
        completed: rem.completed,
        raw: rem,
      };

    });
    return [...medicationEvents, ...reminderEvents];
  }, [medication.medicationList, reminders.remindersList]);

 
  // =========================================================================
  // 2. LOCAL VIEW STATE
  // =========================================================================
  const [currentView, setCurrentView] = useState<View>(Views.MONTH);
  const [currentDate, setCurrentDate] = useState<Date>(new Date());

  // =========================================================================
  // 3. MODAL CONTENT GENERATOR
  // =========================================================================
  const renderModalContent = (
    initialData: Record<string, string>,
    isEditing: boolean,
    editingEventId: string | null = null,
    isCompleted: boolean = false
  ) => (
    <div className="calendar-modal-content">
      <h3 className="calendar-modal-title">
        {isEditing ? 'Edit Entry' : 'Add Event or Medication'}
      </h3>

      <FormFactory
        config="reminder"
        initialData={initialData}
        isLoading={isActionInFlight}
        activeError={null}
        submitLabel={isEditing ? 'Update Event' : 'Save Event'}
        onSubmit={(values) => {
          const isMedication = values.reminder_type === "medication";
          if (isMedication){
            const medicationPayload = {
              name: values.title,
              instructions: values.notes || "",
              start_date: values.startDate,
              end_date: values.endDate || values.startDate,
              is_active: !isCompleted,
            };

            if(isEditing && editingEventId){
              medicationActions.modifyMedication(editingEventId, medicationPayload);
            } else {
              medicationActions.addMedication(medicationPayload);
            }
          } else {
            const time = values.startTime && values.startTime.trim() !== "" ? values.startTime : '00:00';
            const remindAt = new Date(`${values.startDate}T${time}`).toISOString();

            const reminderPayload = {
              title: values.title,
              body: values.notes || "",
              reminder_type: values.reminder_type || "appointment",
              remind_at: remindAt
            }

            if (isEditing && editingEventId){
              reminderActions.modifyReminder(editingEventId,reminderPayload);
            } else {
              reminderActions.scheduleReminder(reminderPayload);
            }
          }
          closeModal();
        }}
        />

      {isEditing && (
        <div className="calendar-modal-actions">
          <button
            type="button"
            className="calendar-btn-delete"
            onClick={() => {
              if(!editingEventId) return;
              const isMedication = initialData.reminder_type === "medication";
              const itemType = isMedication ? "medication" : "reminder";
              const itemName = initialData.title || "this item";
              openModal(
                <DeleteConfirm 
                  id={editingEventId}
                  name={itemName}
                  type={itemType}
                  onCancel={() => closeModal()}
                  onDeleteConfirm={(id) => {
                    if(isMedication){
                      medicationActions.removeMedication(id);
                    } else {
                      reminderActions.removeReminder(id)
                    }
                    closeModal();
                  }}
                  />
              );
            }}
            disabled={isActionInFlight}
          >
            Delete
          </button>

          {!isCompleted && (
            <button
              type="button"
              className="calendar-btn-complete"
              onClick={() => {
                if(editingEventId){
                  const isMedication = initialData.reminder_type === "medication";
                  if(isMedication){
                    medicationActions.modifyMedication(editingEventId, {
                      name: initialData.title,
                      instructions: initialData.notes || "",
                      start_date: initialData.startDate,
                      end_date: initialData.endDate || initialData.startDate,
                      is_active: false,
                    })
                  } else {
                    reminderActions.markAsComplete(editingEventId);
                    
                  }
                  closeModal();
                }
              }}
              disabled={isActionInFlight}
            >
              Complete
            </button>
          )}
        </div>
      )}
    </div>
  );

  const handleSelectSlot = ({ start, end }: { start: Date; end: Date }) => {
    const initialData = {
      reminder_type: 'medication',
      title: '',
      startDate: format(start, 'yyyy-MM-dd'),
      startTime: format(start, 'HH:mm'),
      endDate: format(end, 'yyyy-MM-dd'),
      endTime: format(end, 'HH:mm'),
      notes: '',
    };

    openModal(renderModalContent(initialData, false));
  };

  const handleSelectEvent = (event: CalendarEvent) => {
    const initialData = {
      reminder_type: event.type,
      title: event.title,
      startDate: format(event.start, 'yyyy-MM-dd'),
      startTime: format(event.start, 'HH:mm'),
      endDate: format(event.end, 'yyyy-MM-dd'),
      endTime: format(event.end, 'HH:mm'),
      notes: event.notes || "",
    };

    openModal(renderModalContent(initialData, true, event.id, event.completed));
  };

  // =========================================================================
  // 5. CUSTOM AGENDA COMPONENTS
  // =========================================================================
  const customComponents = {
    agenda: {
      date: ({ day, label }: { day: Date; label: string }) => {
        const dayEvents = events.filter(
          (evt) => format(evt.start, 'yyyy-MM-dd') === format(day, 'yyyy-MM-dd')
        );
        return (
          <button
            type="button"
            className="calendar-agenda-date-btn"
            onClick={() => {
              if (dayEvents.length > 0) {
                handleSelectEvent(dayEvents[0]);
              } else {
                handleSelectSlot({ start: day, end: addHours(day, 1) });
              }
            }}
          >
            🗓️ {label}
          </button>
        );
      },
      event: ({ event }: { event: CalendarEvent }) => (
        <span
          onClick={() => handleSelectEvent(event)}
          className={`calendar-agenda-event ${event.completed ? 'completed' : ''}`}
        >
          {event.title} {event.notes ? `(${event.notes})` : ''}
          {event.completed && ' ✓'}
        </span>
      ),
    },
  };

  // =========================================================================
  // 6. RENDER TREE
  // =========================================================================
  if (isPending) return <LoadingSpinner />
  if (hasError) return <ErrorState error={errorMessage}/>;

  return (
    <div className="calendar-view-container">
      <Calendar
        localizer={localizer}
        events={events}
        startAccessor="start"
        endAccessor="end"
        views={[Views.MONTH, Views.WEEK, Views.DAY, Views.AGENDA]}
        view={currentView}
        date={currentDate}
        onView={(view) => setCurrentView(view)}
        onNavigate={(date) => setCurrentDate(date)}
        selectable={true}
        onSelectSlot={handleSelectSlot}
        onSelectEvent={handleSelectEvent}
        components={customComponents}
        eventPropGetter={(event) => {
          const completedClass = event.completed ? 'completed' : '';
          const typeClass = event.type === 'medication' ? 'type-medication' : 'type-other';
          return {
            className: `calendar-event-tile ${completedClass} ${typeClass}`,
          };
        }}
      />
    </div>
  );
}





