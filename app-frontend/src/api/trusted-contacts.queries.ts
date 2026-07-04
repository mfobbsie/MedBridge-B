import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { TrustedContactCreate, TrustedContactResponse, TrustedContactUpdate } from "../types/features";
import { apiHelper } from "./apiHelper";




export const useListTrustedContacts = () => {
    return useQuery<TrustedContactResponse[]>({
        queryKey: ["trusted-contacts"],
        queryFn: () => {
            return apiHelper({
                url: "/trusted-contacts",
                method: "GET",
                body: null
            })
        }
    })
}


export const useAddTrustedContact = () => {
    const queryClient = useQueryClient();
    return useMutation<TrustedContactResponse, Error, TrustedContactCreate>({
        mutationFn: (body) => {
            return apiHelper({
                url: "/trusted-contacts",
                method: "POST",
                body: body
            })
        },
        onSuccess: (data) => {
            console.log("Trusted Contact successfully created.", data)
            queryClient.invalidateQueries({ queryKey: ["trusted-contacts"] })

        },
        onError: (error) => {
            console.error("Error creating trusted contact.", error)
        }
    })
}


export const useUpdateTrustedContact = () => {
    const queryClient = useQueryClient();
    return useMutation<TrustedContactResponse, Error, { contact_id: string, body: TrustedContactUpdate }>({
        mutationFn: ({ contact_id, body }) => {
            return apiHelper({
                url: `/trusted-contacts/${contact_id}`,
                method: "PATCH",
                body: body
            })
        },
        onSuccess: (data, { contact_id }) => {
            console.log(`Contact ${contact_id} has been successfuly updated.`, data);
            queryClient.invalidateQueries({ queryKey: ["trusted-contacts"] })
        },
        onError: (error) => {
            console.error("Error with updating contact", error);
        }

    })
}


export const useRemoveTrustedContact = () => {
    const queryClient = useQueryClient();
    return useMutation<void, Error, string>({
        mutationFn: ( contact_id:string ) => {
            return apiHelper({
                url: `/trusted-contacts/${contact_id}`,
                method: "DELETE",
                body:null
            })
        },
        onSuccess: () => {
            console.log("Contact has been successfully deleted");
            queryClient.invalidateQueries({ queryKey: ["trusted-contacts"] })
        },
        onError: (error) => {
            console.error("Error with deleting contact", error);
        }

    })
}

