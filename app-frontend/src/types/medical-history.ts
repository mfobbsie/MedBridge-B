export interface TrustedContact {
  id: string;
  label: string;
  name: string;
}

export interface Provider {
  id: string;
  name: string;
  specialty: string;
}

export interface DocumentItem {
  id: string;
  filename: string;
  uploaded_at: string;
}

export interface ChartEntry {
  id: string;
  label: string;
  value: number;
  recorded_at: string;
}

export interface Medication {
  id: string;
  name: string;
  dosage: string;
  frequency: string;
  start_date: string;
  end_date?: string;
}

export interface UserProfile {
  id: string;
  name: string;
  email: string;
  language?: string;
}
