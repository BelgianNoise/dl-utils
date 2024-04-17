import { DLRequestPlatform } from './dl-request-platform';
import { DLRequestStatus } from './dl-request-status';

export interface DLRequest {
  id: number;
  status: DLRequestStatus;
  platform: DLRequestPlatform;
  created: Date;
  updated: Date;
  mpdOrM3u8Url: string;
  mpdOrM3u8Content: string;
}
