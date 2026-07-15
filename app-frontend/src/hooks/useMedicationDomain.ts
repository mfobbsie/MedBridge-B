import {
  useCreateMedication,
  useDeleteMedication,
  useGetMedication,
  useListMedications,
  useReplaceMedication,
  useUpdateMedication,
} from "../api/medication.queries";

export const useMedicationDomain = (medication_id?: string) => {
  const {
    data: medicationListData,
    isPending: listPending,
    isError: isListError,
    error: listError,
  } = useListMedications();

  const {
    data: medicationData,
    isPending: singlePending,
    isError: isSingleError,
    error: singleError,
  } = useGetMedication(medication_id || "");

  const {
    mutate: createMutation,
    isPending: createPending,
    isError: isCreateError,
    error: createError,
  } = useCreateMedication();

  const {
    mutate: updateMutation,
    isPending: updatePending,
    variables: updateVars,
    isError: isUpdateError,
    error: updateError,
  } = useUpdateMedication();

  const {
    mutate: replaceMutation,
    isPending: replacePending,
    variables: replaceVars,
    isError: isReplaceError,
    error: replaceError,
  } = useReplaceMedication();

  const {
    mutate: deleteMutation,
    isPending: deletePending,
    isError: isDeleteError,
    variables: deletingId,
    error: deleteError,
  } = useDeleteMedication();

  const isPending = listPending || (!!medication_id && singlePending);

  const hasError =
    isListError ||
    isCreateError ||
    isUpdateError ||
    isReplaceError ||
    isDeleteError ||
    isSingleError;

  const errorMessage =
    listError?.message ||
    singleError?.message ||
    createError?.message ||
    updateError?.message ||
    replaceError?.message ||
    deleteError?.message ||
    "An unexpected issue has occured within the medicaton Domain.";

  const currentMedications = (medicationListData || []).filter(
    (medication: any) => medication?.is_active !== false,
  );
  const pastMedications = (medicationListData || []).filter(
    (medication: any) => medication?.is_active === false,
  );

  const isMedicationListEmpty =
    !listPending &&
    !listError &&
    !singlePending &&
    !singleError &&
    !medicationData &&
    (!medicationListData || medicationListData.length === 0);

  const viewConfigs = {
    scheduleWorkspace: {
      title: "Medication Schedule",
      description: "Keep track of all your medications and when to take them.",
      icon: "⏰",
    },
    emptyWorkspace: {
      title: "Nothing to take!",
      description: "You have no medications listed",
      icon: "👏",
    },
    creationForm: {
      title: "Add new Medication",
      description: "Add new medications so that you never miss a dose.",
      icon: "💊",
    },
  };

  return {
    data: {
      medicationList: medicationListData || [],
      rawResponse: medicationListData,
      medication: medicationData,
      current: currentMedications,
      past: pastMedications,
    },

    flags: {
      isPending,
      hasError,
      errorMessage,
      isMedicationListEmpty,
      isCreating: createPending,
      isUpdating: updatePending ? updateVars?.medication_id : null,
      isReplacing: replacePending ? replaceVars?.medication_id : null,
      isDeleting: deletePending ? deletingId : null,
      isActionInFlight:
        createPending || updatePending || replacePending || deletePending,
    },

    actions: {
      addMedication: (body: any) => createMutation(body),
      modifyMedication: (medication_id: string, body: any) =>
        updateMutation({ medication_id, body }),
      replaceMedication: (medication_id: string, body: any) =>
        replaceMutation({ medication_id, body }),
      removeMedication: (medication_id: string) =>
        deleteMutation(medication_id),
    },

    viewConfigs,
  };
};
