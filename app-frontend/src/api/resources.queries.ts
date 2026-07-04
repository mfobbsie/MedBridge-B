import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { apiHelper } from "./apiHelper";
import type { ResourceResponse } from "../types/features";

import type { HealthScoreResponse } from "../types/features";




export const useListResources = (filters: { resource_type?: string; tag?: string } = {}) => {
    const { resource_type, tag } = filters;

    // Construct the query parameters cleanly
    const params = new URLSearchParams();
    if (resource_type) params.append("resource_type", resource_type);
    if (tag) params.append("tag", tag);

    const queryString = params.toString();
    const url = queryString ? `/resources?${queryString}` : "/resources";

    return useQuery<ResourceResponse[]>({
        // Tracking filters in the queryKey ensures the cache separates different filter views automatically
        queryKey: ["resources", { resource_type, tag }],
        queryFn: () => {
            return apiHelper({
                url,
                method: "GET",
                body: null
            });
        }
    });
};



export const useGetResource = (resource_id: string) => {
    return useQuery<ResourceResponse>({
        queryKey: ["resources", resource_id],
        queryFn: () => {
            return apiHelper({
                url: `/resources/${resource_id}`,
                method: "GET",
                body: null
            })
        }
    })
}


export const useListHealthScores = () => {
    return useQuery<HealthScoreResponse[]>({
        queryKey: ["health-scores"],
        queryFn: () => {
            return apiHelper({
                url: "/health-scores",
                method: "GET",
                body: null
            })
        }
    })
}


export const useGenerateHealthScore = () => {
    const queryClient = useQueryClient();
    return useMutation<HealthScoreResponse, Error, string>({
        mutationFn: (document_id: string) => {
            return apiHelper({
                url: `/documents/${document_id}/health-score`,
                method: "POST",
                body: null,
            })
        },
        onSuccess: (data) => {
            console.log("Health score has been generated", data)
            queryClient.invalidateQueries({ queryKey: ["health-scores"] })

        },
        onError: (error) => {
            console.error("Error generating health score", error)
        }

    })
}