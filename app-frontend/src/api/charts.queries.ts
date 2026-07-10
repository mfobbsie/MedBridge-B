import { useQuery } from "@tanstack/react-query";
import { apiHelper } from "./apiHelper";

export interface ChartEntry {
  id: string;
  label: string;
  value: number;
  recorded_at: string;
}

export interface ChartsResponse {
  charts: ChartEntry[];
}

export const useGetCharts = (user_id: string) => {
  return useQuery<ChartsResponse>({
    queryKey: ["charts", user_id],
    queryFn: () => {
      return apiHelper({
        url: `http://localhost:8000/charts?user_id=${user_id}`,
        method: "GET",
        body: null,
      });
    },
  });
};
