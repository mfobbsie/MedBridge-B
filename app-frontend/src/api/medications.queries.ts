import { useQuery } from "@tanstack/react-query";
import { apiHelper } from "./apiHelper";

export interface Medication {
  id: string;
  name: string;
  dosage: string;
  frequency: string;
  start_date: string;
  end_date?: string;
}

export interface MedicationsResponse {
  current: Medication[];
  past: Medication[];
}

export const useGetMedications = (user_id: string) => {
  return useQuery<MedicationsResponse>({
    queryKey: ["medications", user_id],
    queryFn: () => {
      return apiHelper({
        url: `http://localhost:8000/medications?user_id=${user_id}`,
        method: "GET",
        body: null,
      });
    },
  });
};
