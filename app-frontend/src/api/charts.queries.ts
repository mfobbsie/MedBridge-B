import { useQuery } from "@tanstack/react-query";
import { apiHelper } from "./apiHelper";

import { API_BASE_URL as BASE_URL } from "../config/env";

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
        url: `${BASE_URL}/charts?user_id=${user_id}`,
        method: "GET",
        body: null,
      });
    },
  });
};
