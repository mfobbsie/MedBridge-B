import {
    useListReminders,
    useCreateReminder,
    useCompleteReminder,
    useDeleteReminder,
    useUpdateReminder
} from "../api/reminders.queries"
import { LoadingSpinner } from "./LoadingSpinner";



export const ApiSandbox = () => {

    const { data: reminders, isLoading, isError } = useListReminders();
    const { mutate: createReminder } = useCreateReminder();
    const { mutate: updateReminder } = useUpdateReminder();
    const { mutate: deleteReminder } = useDeleteReminder();
    const { mutate: completeReminder } = useCompleteReminder();


    const targetId = reminders?.[0]?.reminder_id || "";


    { if (isLoading) return <LoadingSpinner /> }

    { if (isError) return <h1> Error has occured. </h1> }

    { if (reminders?.length === 0) return <h1>No reminders.</h1> }


    return (
        <>
            <pre>
                {JSON.stringify(reminders, null, 2)}
            </pre>

            <button onClick={() => createReminder({
                title: "Sandbox Test Reminder",
                reminder_type: "Medication",
                remind_at: new Date().toISOString(),
            })}> + Create Reminder
            </button>


            <button onClick={() => updateReminder({
                reminder_id: targetId,
                body: { title: "updated Sandbox Title!" }
            })}
                disabled={!targetId}> ✏️ Update Reminder
            </button>



            <button onClick={() => completeReminder(targetId)}
                disabled={!targetId}>
                ✅ Complete Reminder
            </button>


            <button onClick={() => deleteReminder(targetId)}
                disabled={!targetId}>
                🗑️ Delete Reminder
            </button>

        </>

    )



}