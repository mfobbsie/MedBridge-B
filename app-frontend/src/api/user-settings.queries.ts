import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { apiHelper } from "./apiHelper"

const BASE_URL = import.meta.env.VITE_API_URL;

export interface UserSettingsResponse {
  id: string;
  allow_trusted_contacts: boolean;
  allow_mychart_integration: boolean;
  enable_reminders: boolean;
  updated_at: string;
}

export interface UpdateUserSettings {
    allow_trusted_contacts: boolean | null;
    allow_mychart_integration: boolean | null;
    enable_reminders: boolean | null;
}

export const useGetUserSettings = (user_id: string) => {
    return useQuery<UserSettingsResponse>({
        queryKey: ["user-settings", user_id],
        queryFn: () => {
            return apiHelper({
                url: `${BASE_URL}/user-settings/?user_id=${user_id}`,
                method: "GET",
                body: null
            })
        },
        enabled: !!user_id
    })

}

export const useUpdateUserSettings = (user_id: string) => {
    const queryClient = useQueryClient();

    return useMutation<UserSettingsResponse, Error, UpdateUserSettings>({
        mutationFn: (body) => {
            return apiHelper({
                url: `${BASE_URL}/user-settings/?user_id=${user_id}`,
                method: "PATCH",
                body: body
            })
        },
        onSuccess: (data) => {
            console.log(`User ${user_id} settings have been updated.`, data)
            queryClient.invalidateQueries({ queryKey: ["user-settings", user_id] })

        },
        onError: (error) => {
            console.error("Failed to update user settings.", error)
        }


    })

}
