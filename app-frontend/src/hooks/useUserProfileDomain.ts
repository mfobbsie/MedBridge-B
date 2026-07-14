import { useGetUserProfile } from "../api/user-profile.queries";

export const useUserProfileDomain = (user_id: string) => {
  const {
    data: profileData,
    isPending,
    isError,
    error,
  } = useGetUserProfile(user_id);

  const hasError = isError;
  const errorMessage =
    error?.message || "Failed to load user profile information.";

  const isProfileEmpty =
    !isPending &&
    !isError &&
    (!profileData || Object.keys(profileData).length === 0);

  return {
    data: {
      profile: profileData || {},
      rawResponse: profileData,
    },
    flags: {
      isPending,
      hasError,
      errorMessage,
      isProfileEmpty,
    },
    actions: {},
    viewConfigs: {
      profileSection: {
        title: "User Profile",
        description: "Your personal account details.",
        icon: "👤",
      },
    },
  };
};
