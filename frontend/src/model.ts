export interface MeshHeader {
  blockIndices: number[];
  [key: string]: any; 
}

export interface ScanMetadata {
  id: string;
  modelUrl: string;
  format: string;
  timestamp: string;
}