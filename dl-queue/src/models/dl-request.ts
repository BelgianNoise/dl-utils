import { getPool } from '../utils/database';
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

export async function addDownloadRequestToDatabase(
  downloadRequest: DLRequest,
): Promise<DLRequest> {
  // Force new requests to have status 'PENDING'
  downloadRequest.status = DLRequestStatus.PENDING;
  // Set the created and updated dates
  downloadRequest.created = new Date();
  downloadRequest.updated = new Date();

  // Add the request to the database
  const result = await getPool().query<{ id: number }>(`
    INSERT INTO dl.dl_request (
      status,
      platform,
      video_page_or_manifest_url,
      created,
      updated,
      output_filename,
      preferred_quality_matcher
    ) VALUES (
      $1, $2, $3, $4, $5, $6, $7
    ) RETURNING id
  `, [
    downloadRequest.status,
    downloadRequest.platform,
    downloadRequest.videoPageOrManifestUrl,
    downloadRequest.created,
    downloadRequest.updated,
    downloadRequest.outputFilename,
    downloadRequest.preferredQualityMatcher,
  ]);

  downloadRequest.id = result.rows[0].id;

  return downloadRequest;
}

export async function urlIsAlreadyPending(url: string): Promise<boolean> {
  const result = await getPool().query<{ count: number }>(`
    SELECT COUNT(*) FROM dl.dl_request
    WHERE video_page_or_manifest_url = $1 AND status = $2
  `, [url, DLRequestStatus.PENDING]);

  return result.rows[0].count > 0;
}
