import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiHelper } from "./apiHelper";
import type { ProviderCreate, ProviderResponse, ProviderUpdate } from "../types/features";

const BASE_URL = import.meta.env.VITE_API_URL;

export const useListProviders = () => {
    return useQuery<ProviderResponse[]>({
        queryKey: ["providers"],
        queryFn: () => {
            return apiHelper({
                url: `${BASE_URL}/providers`,
                method: "GET",
                body: null
            })
        }
    })
}

export const useAddProvider = () => {
    const queryClient = useQueryClient();
    return useMutation<ProviderResponse, Error, ProviderCreate>({
        mutationFn: (body) => {
            return apiHelper({
                url: `${BASE_URL}/providers`,
                method: "POST",
                body: body
            })
        },
        onSuccess: (data) => {
            console.log("Provider successfully created.", data)
            queryClient.invalidateQueries({ queryKey: ["providers"] })

        },
        onError: (error) => {
            console.error("Error creating provider.", error)
        }
    })
}

export const useUpdateProvider = () => {
    const queryClient = useQueryClient();
    return useMutation<ProviderResponse, Error, { provider_id: string, body: ProviderUpdate }>({
        mutationFn: ({ provider_id, body }) => {
            return apiHelper({
                url: `${BASE_URL}/providers/${provider_id}`,
                method: "PATCH",
                body: body
            })
        },
        onSuccess: (data, { provider_id }) => {
            console.log(`Provider ${provider_id} has been successfuly updated.`, data);
            queryClient.invalidateQueries({ queryKey: ["providers"] })
        },
        onError: (error) => {
            console.error("Error with updating provider", error);
        }

    })
}

export const useDeleteProvider = () => {
    const queryClient = useQueryClient();
    return useMutation<void, Error, string>({
        mutationFn: ( provider_id:string ) => {
            return apiHelper({
                url: `${BASE_URL}/providers/${provider_id}`,
                method: "DELETE",
                body:null
            })
        },
        onSuccess: () => {
            console.log("Provider has been successfully deleted");
            queryClient.invalidateQueries({ queryKey: ["providers"] })
        },
        onError: (error) => {
            console.error("Error with deleting provider", error);
        }

    })
}

