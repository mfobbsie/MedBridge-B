import { useQuery } from "@tanstack/react-query";
import { apiHelper } from "./apiHelper";

export interface UserProfileResponse {
  id: string;
  name: string;
  email: string;
  language?: string;
  created_at: string;
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
