import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiHelper } from "./apiHelper";

export interface UpdateUserProfilePayload {
  full_name?: string;
  email?: string;
  preferred_language?: string;
  explanation_level?: number; // 0 = plain, 1 = detailed
}

export const useGetUserProfile = (user_id: string) => {
  return useQuery<UserProfileResponse>({
    queryKey: ["user-profile", user_id],
    queryFn: () => {
      return apiHelper({
        url: `http://localhost:8000/user/profile?user_id=${user_id}`,
        method: "GET",
        body: null,
      });
    },
  });
};
// UPDATE USER PROFILE (PATCH)
export const useUpdateUserProfile = (user_id: string) => {
  const queryClient = useQueryClient();

  return useMutation<UserProfileResponse, Error, UpdateUserProfilePayload>
({
    mutationFn: (body) => {
      return apiHelper({
        url: `http://localhost:8000/user/profile?user_id=${user_id}`,
        method: "PATCH",
        body,
      });
    },

    onSuccess: () => {
      // Refresh profile data after update
      queryClient.invalidateQueries({
        queryKey: ["user-profile", user_id],
      });
    },

    onError: (error) => {
      console.error("Failed to update user profile:", error);
    },
  });
};
