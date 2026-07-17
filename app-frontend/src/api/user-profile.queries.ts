import { useQuery } from "@tanstack/react-query";
import { apiHelper } from "./apiHelper";

const BASE_URL = import.meta.env.VITE_API_URL;

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
        url: `${BASE_URL}/user/profile?user_id=${user_id}`,
        method: "GET",
        body: null,
      });
    },
  });
};
