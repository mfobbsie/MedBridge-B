import { useGetCharts } from "../api/charts.queries";

export const useChartsDomain = (user_id: string) => {
  const { data: chartsData, isPending, isError, error } = useGetCharts(user_id);

  const hasError = isError;
  const errorMessage = error?.message || "Failed to load medical charts.";

  const isChartsEmpty =
    !isPending && !isError && (!chartsData || chartsData.charts.length === 0);

  return {
    data: {
      charts: chartsData?.charts || [],
      rawResponse: chartsData,
    },
    flags: {
      isPending,
      hasError,
      errorMessage,
      isChartsEmpty,
    },
    actions: {},
    viewConfigs: {
      chartsSection: {
        title: "Medical Charts",
        description: "Your recorded health metrics and chart history.",
        icon: "📊",
      },
    },
  };
};
