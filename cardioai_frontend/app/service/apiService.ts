export interface AccelerometerDataPoint {
  ax: number;
  ay: number;
  az: number;
  timestamp: number;
}

export interface DeviceInfo {
  model: string;
  platform: string;
}
