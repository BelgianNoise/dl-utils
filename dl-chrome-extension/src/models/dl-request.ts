import { DLRequestPlatform } from './dl-request-platform';
import { DLRequestStatus } from './dl-request-status';

export interface DLRequest {
  id: number;
  status: DLRequestStatus;
  platform: DLRequestPlatform;
  videoPageOrManifestUrl: string;
  created: Date;
  updated: Date;
  outputFilename: string | undefined;
  preferredQualityMatcher: string | undefined;
}
