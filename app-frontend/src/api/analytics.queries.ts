import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiHelper } from "./apiHelper";

export interface FeedbackSubmit {
    summary_id: string;
    rating: number;
    feedback_text?: string;
}

export interface EventLog {
    event_type: string;
    event_category: string;
    event_data?: Record<string, string>;
    session_id?: string;
    response_time_ms?: number;
    success?: boolean;
}


export interface UserSettingsUpdate {
    preferred_language?: string;
    accessibility_mode?: boolean;
    low_bandwidth_mode?: boolean;
    notification_enabled?: boolean;
}



export const useSubmitFeedback = () => {
    const queryClient = useQueryClient();

    return useMutation<void, Error, FeedbackSubmit>({
        mutationFn: (body: FeedbackSubmit) => {
            return apiHelper({
                url: "http://localhost:8000/analytics/feedback",
                method: "POST",
                body: body,
            });

        },
        onSuccess: (data) => {
            console.log("Feedback successful:", data);
            queryClient.invalidateQueries({ queryKey: ["analytics", "feedback"] })
        },

        onError: (error) => {
            console.error("Feedback failed:", error)
        },

    });

};


export const useLogEvent = () => {
    const queryClient = useQueryClient();

    return useMutation<void, Error, EventLog>({
        mutationFn: (body: EventLog) => {
            return apiHelper({
                url: "http://localhost:8000/analytics/events",
                method: "POST",
                body: body,
            });
        },

        onSuccess: (data) => {
            console.log("Event successfully set:", data);
            queryClient.invalidateQueries({ queryKey: ["analytics", "events"] })
        },

        onError: (error) => {
            console.error("Event Post failed:", error)
        }
    })
}


export const useGetUserSettings = () => {
    return useQuery({
        queryKey: ["analytics", "settings"],
        queryFn: () => {
            return apiHelper({
                url: "http://localhost:8000/analytics/settings",
                method: "GET",
                body: null,
            })
        },
    })
}


export const useUpdateUserSettings = () => {
    const queryClient = useQueryClient();

    return useMutation<void, Error, UserSettingsUpdate>({
        mutationFn: (body: UserSettingsUpdate) => {
            return apiHelper({
                url: "http://localhost:8000/analytics/settings",
                method: "PATCH",
                body: body,
            });
        },
        onSuccess: (data) => {
            console.log("User settings successfully changed:", data)
            queryClient.invalidateQueries({ queryKey: ["analytics", "settings"] })

        },

        onError: (error) => {
            console.error("Error updating user settings:", error);
        }

    })
}


export const usePatientDashboard = () => {
    return useQuery({
        queryKey: ["analytics", "dashboard", "patient"],
        queryFn: () => {
            return apiHelper({
                url: "http://localhost:8000/analytics/dashboard/patient",
                method: "GET",
                body: null,
            })
        }
    })
}


export const useStakeholderDashboard = () => {
    return useQuery({
        queryKey: ["analytics", "dashboard", "stakeholder"],
        queryFn: () => {
            return apiHelper({
                url: "http://localhost:8000/analytics/dashboard/stakeholder",
                method: "GET",
                body: null,
            })
        }
    })
}


export const useTeamDashboard = () => {
    return useQuery({
        queryKey: ["analytics", "dashboard", "team"],
        queryFn: () => {
            return apiHelper({
                url: "http://localhost:8000/analytics/dashboard/team",
                method: "GET",
                body: null,
            })
        }
    })
}


export const useProviderReadinessDashboard = () => {
    return useQuery({
        queryKey: ["analytics", "dashboard", "provider-readiness"],
        queryFn: () => {
            return apiHelper({
                url: "http://localhost:8000/analytics/dashboard/provider-readiness",
                method: "GET",
                body: null,
            })
        }
    })
}
