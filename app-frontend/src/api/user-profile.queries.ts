import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiHelper } from "./apiHelper";
import type { UserProfile } from "../types/auth";

export interface UpdateUserProfilePayload {
  full_name?: string;
  email?: string;
  preferred_language?: string;
  explanation_level?: number;
}

// GET patient profile
export const useGetUserProfile = () => {
  return useQuery<UserProfile>({
    queryKey: ["patient-profile"],
    queryFn: () =>
      apiHelper({
        url: "http://localhost:8000/patient-profile",
        method: "GET",
        body: null,
      }),
  });
};

// PATCH patient profile
export const useUpdateUserProfile = () => {
  const queryClient = useQueryClient();

  return useMutation<UserProfile, Error, UpdateUserProfilePayload>({
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
