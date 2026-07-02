import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiCall } from "./apiHelper";

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

    return useMutation({
        mutationFn: (body: FeedbackSubmit) => {
            return apiCall({
                url: "/analytics/feedback",
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


export const useSubmitLogEvent = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (body: EventLog) => {
            return apiCall({
                url: "/analytics/events",
                method: "POST",
                body: body,
            });
        },

        onSuccess: (data) => {
            console.log("Event sucessfully set:", data);
            queryClient.invalidateQueries({ queryKey: ["analytics", "events"] })
        },

        onError: (error) => {
            console.error("Event Post failed:", error)
        }
    })
}


export const useSettings = () => {
    return useQuery({
        queryKey: ["analytics", "settings"],
        queryFn: () => {
            return apiCall({
                url: "/analytics/settings",
                method: "GET",
                body: null,
            })
        },
    })
}
