import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiHelper } from "./apiHelper";
import type { UserProfile, UserProfileUpdate } from "../types/auth";

const BASE_URL = import.meta.env.VITE_API_URL;

export interface UserProfileResponse {
  id: string;
  name: string;
  email: string;
  language?: string;
  created_at: string;
}

export const useGetUserProfile = () => {
  return useQuery<UserProfileResponse>({
    queryKey: ["user-profile"],
    queryFn: () => {
      return apiHelper({
        url: `${BASE_URL}/patient-profile`,
        method: "GET",
        body: null,
      });
    },
  });
};

// PATCH patient profile
export const useUpdateUserProfile = () => {
  const queryClient = useQueryClient();

  return useMutation<UserProfile, Error, UserProfileUpdate>({
    mutationFn: (body) =>
      apiHelper({
        url: "http://localhost:8000/patient-profile",
        method: "PATCH",
        body,
      }),

    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["patient-profile"],
      });
    },

    onError: (error) => {
      console.error("Failed to update user profile:", error);
    },
  });
};
