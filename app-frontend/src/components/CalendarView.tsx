import { useState } from 'react';
import { Calendar, dateFnsLocalizer, Views, type View } from 'react-big-calendar';
import { format, parse, startOfWeek, getDay, addHours } from 'date-fns';
import { enUS } from 'date-fns/locale';
import 'react-big-calendar/lib/css/react-big-calendar.css';
import type { CalendarEvent} from '../types/features';
import { useModal } from '../context/ModalContext';
import { FormFactory } from './FormFactory';
import { useCalendarDomain } from '../hooks/useCalendarDomain';

const locales = { 'en-US': enUS };
const localizer = dateFnsLocalizer({ format, parse, startOfWeek, getDay, locales });



export default function CalendarView() {
  // =========================================================================
  // 1. ENGINE & CONTEXT INITIALIZATION
  // =========================================================================
  const {
    events,
    isLoading,
    hasError,
    errorMessage,
    isActionInFlight,
    saveEvent,
    deleteEvent,
    completeEvent,
  } = useCalendarDomain();

  const { openModal, closeModal } = useModal();

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
    <div>
      <h3 style={{ marginTop: 0, marginBottom: '16px', fontSize: '1.25rem', fontWeight: 600 }}>
        {isEditing ? 'Edit Entry' : 'Add Event or Medication'}
      </h3>

      <FormFactory
        config="reminder"
        initialData={initialData}
        isLoading={isActionInFlight}
        activeError={null}
        submitLabel={isEditing ? 'Update Event' : 'Save Event'}
        onSubmit={(values) => {
          saveEvent({
            isEditing,  
            editingEventId,
            title: values.title,
            type: values.reminder_type as any,
            notes: values.notes,
            startDate: values.startDate,
            startTime: values.startTime,
            endDate: values.endDate,
            endTime: values.endTime,
          });
          closeModal();
        }}
      />

      {isEditing && (
        <div style={{ display: 'flex', gap: '8px', marginTop: '16px', justifyContent: 'flex-start' }}>
          <button
            type="button"
            onClick={() => {
              deleteEvent(editingEventId);
              closeModal();
            }}
            style={deleteButtonStyle}
            disabled={isActionInFlight}
          >
            Delete
          </button>
          {!isCompleted && (
            <button
              type="button"
              onClick={() => {
                completeEvent(editingEventId);
                closeModal();
              }}
              style={completeButtonStyle}
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
      notes: event.notes,
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
            style={agendaDateButtonStyle}
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
          style={{
            cursor: 'pointer',
            color: event.completed ? '#10b981' : '#2563eb',
            textDecoration: event.completed ? 'line-through' : 'none',
            fontWeight: 500,
          }}
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
  if (isLoading) return <div style={{ padding: '24px' }}>Loading health calendar...</div>;
  if (hasError) return <div style={{ padding: '24px', color: 'red' }}>{errorMessage}</div>;

  return (
    <div style={{ height: '100%', width: '100%', padding: '24px', position: 'relative', boxSizing: 'border-box' }}>
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
        eventPropGetter={(event) => ({
          style: {
            backgroundColor: event.completed ? '#d1fae5' : event.type === 'medication' ? '#eff6ff' : '#fef3c7',
            color: event.completed ? '#065f46' : event.type === 'medication' ? '#1e40af' : '#92400e',
            border: 'none',
            opacity: event.completed ? 0.7 : 1,
          },
        })}
      />
    </div>
  );
}





//!_________________________________________________________

// export default function CalendarView() {
//     const queryClient = useQueryClient();
//     const [currentView, setCurrentView] = useState<View>(Views.MONTH);
//     const [currentDate, setCurrentDate] = useState<Date>(new Date());

//     // Modal & Form States
//     const [isModalOpen, setIsModalOpen] = useState(false);
//     const [isEditing, setIsEditing] = useState(false);
//     const [editingEventId, setEditingEventId] = useState<string | null>(null);
//     const [eventTitle, setEventTitle] = useState('');
//     const [eventType, setEventType] = useState<'medication' | 'appointment' | 'other'>('medication');
//     const [eventNotes, setEventNotes] = useState('');
//     const [startDate, setStartDate] = useState('');
//     const [startTime, setStartTime] = useState('');
//     const [endDate, setEndDate] = useState('');
//     const [endTime, setEndTime] = useState('');

//     // =========================================================================
//     // REACT QUERY BACKEND SYNCHRONIZATION
//     // =========================================================================

//     const { data: rawReminders = [], isLoading, isError } = useQuery<ReminderResponse[]>({
//         queryKey: ['reminders'],
//         queryFn: async () => apiHelper({ url: `${API_BASE_URL}/reminders`, method: 'GET' })
//     });

//     // Parse backend values into front-end event format
//     const events: CalendarEvent[] = rawReminders.map(rem => {
//         const reminderStart = new Date(rem.remind_at);
//         let reminderEnd = new Date(reminderStart.getTime() + 60 * 60 * 1000); // 1-hour fallback default

//         // Attempt to parse out saved end time values from our encoded backend string wrapper
//         if (rem.body && rem.body.includes('__END_TIME__:')) {
//             try {
//                 const parts = rem.body.split('__END_TIME__:');
//                 const endIso = parts[1]?.trim();
//                 if (endIso) {
//                     reminderEnd = new Date(endIso);
//                 }
//             } catch (e) {
//                 console.error("Failed to extract end timestamp context", e);
//             }
//         }

//         // Strip the tracking layout suffix cleaner for display purposes
//         const visibleNotes = rem.body ? rem.body.split('__END_TIME__:')[0].trim() : '';

//         return {
//             id: rem.id,
//             title: rem.title,
//             start: reminderStart,
//             end: reminderEnd,
//             type: (rem.reminder_type === 'medication' || rem.reminder_type === 'appointment') ? rem.reminder_type : 'other',
//             notes: visibleNotes,
//             completed: rem.completed
//         };
//     });

//     const createMutation = useMutation({
//         mutationFn: async (newReminder: any) => apiHelper({
//             url: `${API_BASE_URL}/reminders`,
//             method: 'POST',
//             body: newReminder
//         }),
//         onSuccess: () => {
//             queryClient.invalidateQueries({ queryKey: ['reminders'] });
//             closeModal();
//         }
//     });

//     const updateMutation = useMutation({
//         mutationFn: async ({ id, data }: { id: string; data: any }) => apiHelper({
//             url: `${API_BASE_URL}/reminders/${id}`,
//             method: 'PATCH',
//             body: data
//         }),
//         onSuccess: () => {
//             queryClient.invalidateQueries({ queryKey: ['reminders'] });
//             closeModal();
//         }
//     });

//     const deleteMutation = useMutation({
//         mutationFn: async (id: string) => apiHelper({
//             url: `${API_BASE_URL}/reminders/${id}`,
//             method: 'DELETE'
//         }),
//         onSuccess: () => {
//             queryClient.invalidateQueries({ queryKey: ['reminders'] });
//             closeModal();
//         }
//     });

//     const completeMutation = useMutation({
//         mutationFn: async (id: string) => apiHelper({
//             url: `${API_BASE_URL}/reminders/${id}/complete`,
//             method: 'POST'
//         }),
//         onSuccess: () => {
//             queryClient.invalidateQueries({ queryKey: ['reminders'] });
//             closeModal();
//         }
//     });

//     // =========================================================================
//     // EVENT HANDLERS
//     // =========================================================================

//     // Explicitly typed parameters matching full calendar properties now
//     const handleSelectSlot = ({ start, end }: { start: Date; end: Date }) => {
//         setIsEditing(false);
//         setEditingEventId(null);
//         setStartDate(format(start, 'yyyy-MM-dd'));
//         setStartTime(format(start, 'HH:mm'));
//         setEndDate(format(end, 'yyyy-MM-dd'));
//         setEndTime(format(end, 'HH:mm'));
//         setIsModalOpen(true);
//     };

//     const handleSelectEvent = (event: CalendarEvent) => {
//         setIsEditing(true);
//         setEditingEventId(event.id);
//         setEventTitle(event.title);
//         setEventType(event.type);
//         setEventNotes(event.notes);
//         setStartDate(format(event.start, 'yyyy-MM-dd'));
//         setStartTime(format(event.start, 'HH:mm'));
//         setEndDate(format(event.end, 'yyyy-MM-dd'));
//         setEndTime(format(event.end, 'HH:mm'));
//         setIsModalOpen(true);
//     };

//     const handleSaveEvent = (e: React.FormEvent) => {
//         e.preventDefault();
//         if (!eventTitle.trim()) return;

//         const startCombined = new Date(`${startDate}T${startTime}`).toISOString();
//         const endCombined = new Date(`${endDate}T${endTime}`).toISOString();

//         // Package the end timestamp cleanly into the body/notes string for storage
//         const bodyPayloadWithEndContext = eventNotes.trim()
//             ? `${eventNotes} \n\n__END_TIME__:${endCombined}`
//             : `__END_TIME__:${endCombined}`;

//         const payload = {
//             reminder_type: eventType,
//             title: eventTitle,
//             body: bodyPayloadWithEndContext,
//             remind_at: startCombined,
//             repeat_interval: null
//         };

//         if (isEditing && editingEventId) {
//             updateMutation.mutate({ id: editingEventId, data: payload });
//         } else {
//             createMutation.mutate(payload);
//         }
//     };

//     const handleDeleteEvent = () => {
//         if (editingEventId) deleteMutation.mutate(editingEventId);
//     };

//     const handleCompleteEvent = () => {
//         if (editingEventId) completeMutation.mutate(editingEventId);
//     };

//     const closeModal = () => {
//         setIsModalOpen(false);
//         setIsEditing(false);
//         setEditingEventId(null);
//         setEventTitle('');
//         setEventType('medication');
//         setEventNotes('');
//         setStartDate('');
//         setStartTime('');
//         setEndDate('');
//         setEndTime('');
//     };

//     const customComponents = {
//         agenda: {
//             date: ({ day, label }: { day: Date; label: string }) => {
//                 const dayEvents = events.filter(
//                     evt => format(evt.start, 'yyyy-MM-dd') === format(day, 'yyyy-MM-dd')
//                 );
//                 return (
//                     <button
//                         type="button"
//                         style={agendaDateButtonStyle}
//                         onClick={() => {
//                             if (dayEvents.length > 0) {
//                                 handleSelectEvent(dayEvents[0]);
//                             } else {
//                                 // Calculate safe 1 hour window representation for agenda selection
//                                 const oneHourLater = addHours(day, 1);
//                                 handleSelectSlot({ start: day, end: oneHourLater });
//                             }
//                         }}
//                     >
//                         🗓️ {label}
//                     </button>
//                 );
//             },
//             event: ({ event }: { event: CalendarEvent }) => (
//                 <span
//                     onClick={() => handleSelectEvent(event)}
//                     style={{
//                         cursor: 'pointer',
//                         color: event.completed ? '#10b981' : '#2563eb',
//                         textDecoration: event.completed ? 'line-through' : 'none',
//                         fontWeight: 500
//                     }}
//                 >
//                     {event.title} {event.notes ? `(${event.notes})` : ''}
//                     {event.completed && ' ✓'}
//                 </span>
//             )
//         }
//     };

//     if (isLoading) return <div style={{ padding: '24px' }}>Loading health calendar...</div>;
//     if (isError) return <div style={{ padding: '24px', color: 'red' }}>Failed to sync calendar entries.</div>;

//     return (
//         <div style={{ height: '100%', width: '100%', padding: '24px', position: 'relative', boxSizing: 'border-box' }}>
//             <Calendar
//                 localizer={localizer}
//                 events={events}
//                 startAccessor="start"
//                 endAccessor="end"
//                 views={[Views.MONTH, Views.WEEK, Views.DAY, Views.AGENDA]}
//                 view={currentView}
//                 date={currentDate}
//                 onView={(view) => setCurrentView(view)}
//                 onNavigate={(date) => setCurrentDate(date)}
//                 selectable={true}
//                 onSelectSlot={handleSelectSlot}
//                 onSelectEvent={handleSelectEvent}
//                 components={customComponents}
//                 eventPropGetter={(event) => ({
//                     style: {
//                         backgroundColor: event.completed ? '#d1fae5' : event.type === 'medication' ? '#eff6ff' : '#fef3c7',
//                         color: event.completed ? '#065f46' : event.type === 'medication' ? '#1e40af' : '#92400e',
//                         border: 'none',
//                         opacity: event.completed ? 0.7 : 1
//                     }
//                 })}
//             />

//             {/* Modal Dialog */}
//             {isModalOpen && (
//                 <div style={modalOverlayStyle}>
//                     <div style={modalContentStyle}>
//                         <h3 style={{ marginTop: 0, marginBottom: '16px', fontSize: '1.25rem', fontWeight: 600 }}>
//                             {isEditing ? 'Edit Entry' : 'Add Event or Medication'}
//                         </h3>
//                         <form onSubmit={handleSaveEvent} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
//                             <div>
//                                 <label style={labelStyle}>Type</label>
//                                 <select value={eventType} onChange={(e) => setEventType(e.target.value as any)} style={inputStyle}>
//                                     <option value="medication">💊 Medication</option>
//                                     <option value="appointment">🏥 Appointment</option>
//                                     <option value="other">📝 Other</option>
//                                 </select>
//                             </div>

//                             <div>
//                                 <label style={labelStyle}>Title</label>
//                                 <input type="text" required value={eventTitle} onChange={(e) => setEventTitle(e.target.value)} style={inputStyle} />
//                             </div>

//                             {/* START TIME ROW */}
//                             <div style={{ display: 'flex', gap: '8px' }}>
//                                 <div style={{ flex: 1 }}>
//                                     <label style={labelStyle}>Start Date</label>
//                                     <input type="date" required value={startDate} onChange={(e) => setStartDate(e.target.value)} style={inputStyle} />
//                                 </div>
//                                 <div style={{ flex: 1 }}>
//                                     <label style={labelStyle}>Start Time</label>
//                                     <input type="time" required value={startTime} onChange={(e) => setStartTime(e.target.value)} style={inputStyle} />
//                                 </div>
//                             </div>

//                             {/* END TIME ROW */}
//                             <div style={{ display: 'flex', gap: '8px' }}>
//                                 <div style={{ flex: 1 }}>
//                                     <label style={labelStyle}>End Date</label>
//                                     <input type="date" required value={endDate} onChange={(e) => setEndDate(e.target.value)} style={inputStyle} />
//                                 </div>
//                                 <div style={{ flex: 1 }}>
//                                     <label style={labelStyle}>End Time</label>
//                                     <input type="time" required value={endTime} onChange={(e) => setEndTime(e.target.value)} style={inputStyle} />
//                                 </div>
//                             </div>

//                             <div>
//                                 <label style={labelStyle}>Instructions / Notes</label>
//                                 <textarea value={eventNotes} onChange={(e) => setEventNotes(e.target.value)} style={{ ...inputStyle, height: '60px', resize: 'vertical' }} />
//                             </div>

//                             <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '12px', gap: '8px' }}>
//                                 {isEditing ? (
//                                     <div style={{ display: 'flex', gap: '8px' }}>
//                                         <button type="button" onClick={handleDeleteEvent} style={deleteButtonStyle}>
//                                             Delete
//                                         </button>
//                                         {!events.find(e => e.id === editingEventId)?.completed && (
//                                             <button type="button" onClick={handleCompleteEvent} style={completeButtonStyle}>
//                                                 Complete
//                                             </button>
//                                         )}
//                                     </div>
//                                 ) : <div />}
//                                 <div style={{ display: 'flex', gap: '8px' }}>
//                                     <button type="button" onClick={closeModal} style={cancelButtonStyle}>Cancel</button>
//                                     <button type="submit" style={saveButtonStyle} disabled={createMutation.isPending || updateMutation.isPending}>
//                                         {createMutation.isPending || updateMutation.isPending ? 'Saving...' : 'Save'}
//                                     </button>
//                                 </div>
//                             </div>
//                         </form>
//                     </div>
//                 </div>
//             )}
//         </div>
//     );
// }

// --- Styles ---
const agendaDateButtonStyle: React.CSSProperties = {
    background: 'none', border: 'none', color: '#2563eb', textDecoration: 'underline', cursor: 'pointer', padding: 0, font: 'inherit', textAlign: 'left'
};
const deleteButtonStyle: React.CSSProperties = {
    padding: '8px 12px', borderRadius: '6px', border: 'none', backgroundColor: '#ef4444', color: '#ffffff', cursor: 'pointer', fontWeight: 500, fontSize: '0.9rem'
};
const completeButtonStyle: React.CSSProperties = {
    padding: '8px 12px', borderRadius: '6px', border: 'none', backgroundColor: '#10b981', color: '#ffffff', cursor: 'pointer', fontWeight: 500, fontSize: '0.9rem'
};
const modalOverlayStyle: React.CSSProperties = {
    position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(0, 0, 0, 0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000
};
const modalContentStyle: React.CSSProperties = {
    background: '#ffffff', padding: '24px', borderRadius: '8px', width: '100%', maxWidth: '400px', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)', color: '#1f2937', fontFamily: 'sans-serif'
};
const labelStyle: React.CSSProperties = {
    display: 'block', fontSize: '0.875rem', fontWeight: 500, marginBottom: '4px', color: '#4b5563'
};
const inputStyle: React.CSSProperties = {
    width: '100%', padding: '8px 12px', borderRadius: '6px', border: '1px solid #d1d5db', fontSize: '0.95rem', boxSizing: 'border-box'
};
const cancelButtonStyle: React.CSSProperties = {
    padding: '8px 16px', borderRadius: '6px', border: '1px solid #d1d5db', backgroundColor: '#ffffff', color: '#4b5563', cursor: 'pointer', fontWeight: 500
};
const saveButtonStyle: React.CSSProperties = {
    padding: '8px 16px', borderRadius: '6px', border: 'none', backgroundColor: '#2563eb', color: '#ffffff', cursor: 'pointer', fontWeight: 500
};