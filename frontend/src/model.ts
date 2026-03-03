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

export interface ScanRecord {
  id: string;
  name: string;
  upload_date: string;
  upload_timestamp: string;
  zip_file: string;
}