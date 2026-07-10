import { useGetMedications } from "../api/medications.queries";

export const useMedicationsDomain = (user_id: string) => {
  const {
    data: medsData,
    isPending,
    isError,
    error,
  } = useGetMedications(user_id);

  const hasError = isError;
  const errorMessage = error?.message || "Failed to load medication history.";

  const isMedicationsEmpty =
    !isPending &&
    !isError &&
    (!medsData ||
      (medsData.current.length === 0 && medsData.past.length === 0));

  return {
    data: {
      current: medsData?.current || [],
      past: medsData?.past || [],
      rawResponse: medsData,
    },
    flags: {
      isPending,
      hasError,
      errorMessage,
      isMedicationsEmpty,
    },
    actions: {},
    viewConfigs: {
      medicationsSection: {
        title: "Medication History",
        description: "Your current and past prescriptions.",
        icon: "💊",
      },
    },
  };
};
