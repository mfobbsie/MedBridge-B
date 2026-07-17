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

export const useGetUserSettings = () => {
    return useQuery<UserSettingsResponse>({
        queryKey: ["user-settings"],
        queryFn: () => {
            return apiHelper({
                url: `${BASE_URL}/user-settings/`,
                method: "GET",
                body: null,
            });
        },
    });
};

export const useUpdateUserSettings = () => {
    const queryClient = useQueryClient();

    return useMutation<UserSettingsResponse, Error, UpdateUserSettings>({
        mutationFn: (body) => {
            return apiHelper({
                url: `${BASE_URL}/user-settings/`,
                method: "PATCH",
                body: body
            })
        },
        onSuccess: (data) => {
            console.log(`User settings have been updated.`, data)
            queryClient.invalidateQueries({ queryKey: ["user-settings"] })
        },
        onError: (error) => {
            console.error("Failed to update user settings.", error)
        }


    })

}
