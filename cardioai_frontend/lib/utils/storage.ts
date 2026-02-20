export interface MeasurementEntry {
  id: string;
  timestamp: string;
  source: string;
  data: number[][]; // [time[], signal[]]
}

const STORAGE_KEY = 'heartscan_measurements';

export const storage = {
  saveMeasurement: (entry: MeasurementEntry) => {
    try {
      const existing = storage.getMeasurements();
      const updated = [entry, ...existing].slice(0, 50); // Keep last 50
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
    } catch (e) {
      console.error('Failed to save measurement', e);
    }
  },

  getMeasurements: (): MeasurementEntry[] => {
    if (typeof window === 'undefined') return [];
    try {
      const data = localStorage.getItem(STORAGE_KEY);
      return data ? JSON.parse(data) : [];
    } catch (e) {
      console.error('Failed to load measurements', e);
      return [];
    }
  },

  deleteMeasurement: (id: string) => {
    try {
      const existing = storage.getMeasurements();
      const updated = existing.filter(m => m.id !== id);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
    } catch (e) {
      console.error('Failed to delete measurement', e);
    }
  },

  clearAll: () => {
    localStorage.removeItem(STORAGE_KEY);
  }
};
