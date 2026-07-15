import { useGetUserProfile, useUpdateUserProfile } from "../api/user-profile.queries";

export const useUserProfileDomain = (user_id: string) => {
  const {
    data: profileData,
    isPending: isLoadingProfile,
    isError:isProfileError,
    error: profileError,
  } = useGetUserProfile(user_id);

  const isProfileEmpty =
    !isLoadingProfile &&
    !isProfileError &&
    (!profileData || Object.keys(profileData).length === 0);

  // UPDATE PROFILE
  const {
    mutate: updateProfile,
    isPending: isUpdating,
    isError: isUpdateError,
    error: updateError,
  } = useUpdateUserProfile(user_id);

  // COMBINED ERROR FLAGS
  const hasError = isProfileError || isUpdateError;
  const errorMessage =
    profileError?.message ||
    updateError?.message ||
    "Failed to load or update user profile information.";

  return {
    data: {
      profile: profileData || {},
      rawResponse: profileData,
    },
    flags: {
      isLoadingProfile,
      isUpdating,
      hasError,
      errorMessage,
      isProfileEmpty,
    },
    actions: {
      updateProfile,
      },
    viewConfigs: {
      profileSection: {
        title: "User Profile",
        description: "Your personal account details.",
        icon: "👤",
      },
    },
  };
};
