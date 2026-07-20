import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { apiHelper } from "./apiHelper"
import type { ReminderUpdate, ReminderCreate, ReminderResponse } from "../types/features"

import { API_BASE_URL as BASE_URL } from "../config/env";

export const useListReminders = () => {
    return useQuery<ReminderResponse[]>({
        queryKey: ["reminders"],
        queryFn: () => {
            return apiHelper({
                url: `${BASE_URL}/reminders`,
                method: "GET",
                body: null
            })
        }
    })
}

export const useCreateReminder = () => {
    const queryClient = useQueryClient();
    return useMutation<ReminderResponse, Error, ReminderCreate>({
        mutationFn: (body) => {
            return apiHelper({
                url: `${BASE_URL}/reminders`,
                method: "POST",
                body: body
            })
        },
        onSuccess: (data) => {
            console.log("Reminder successfully created.", data)
            queryClient.invalidateQueries({ queryKey: ["reminders"] })

        },
        onError: (error) => {
            console.error("Error creating reminder.", error)
        }
    })
}

export const useUpdateReminder = () => {
    const queryClient = useQueryClient();
    return useMutation<ReminderResponse, Error, { reminder_id: string, body: ReminderUpdate }>({
        mutationFn: ({ reminder_id, body }) => {
            return apiHelper({
                url: `${BASE_URL}/reminders/${reminder_id}`,
                method: "PATCH",
                body: body
            })
        },
        onSuccess: (data, { reminder_id }) => {
            console.log(`Reminder ${reminder_id} has been successfuly updated.`, data);
            queryClient.invalidateQueries({ queryKey: ["reminders"] })
        },
        onError: (error) => {
            console.error("Error with updating reminder", error);
        }

    })
}

export const useDeleteReminder = () => {
    const queryClient = useQueryClient();
    return useMutation<void, Error, string>({
        mutationFn: ( reminder_id:string ) => {
            return apiHelper({
                url: `${BASE_URL}/reminders/${reminder_id}`,
                method: "DELETE",
                body:null
            })
        },
        onSuccess: () => {
            console.log("Reminder has been successfully deleted");
            queryClient.invalidateQueries({ queryKey: ["reminders"] })
        },
        onError: (error) => {
            console.error("Error with deleting reminder", error);
        }

    })
}

export const useCompleteReminder = () => {
    const queryClient = useQueryClient();
    return useMutation<void, Error, string>({
        mutationFn: ( reminder_id:string ) => {
            return apiHelper({
                url: `${BASE_URL}/reminders/${reminder_id}/complete`,
                method: "POST",
                body:null
            })
        },
        onSuccess: () => {
            console.log("Reminder has been successfully completed");
            queryClient.invalidateQueries({ queryKey: ["reminders"] })
        },
        onError: (error) => {
            console.error("Error with completing reminder", error);
        }

    })
}