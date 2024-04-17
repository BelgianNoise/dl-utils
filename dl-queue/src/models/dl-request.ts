import { getPool } from '../utils/database';
import { DLRequestPlatform } from './dl-request-platform';
import { DLRequestStatus } from './dl-request-status';

export interface DLRequest {
  id: number;
  status: DLRequestStatus;
  platform: DLRequestPlatform;
  videoPageUrl: string;
  created: Date;
  updated: Date;
  mpdOrM3u8Url: string;
  outputFilename: string;
  preferredQualityMatcher: string | undefined;
  drmToken: string | undefined;
}

export interface DLRequestManifestContent {
  id: number;
  dl_request_id: number;
  content: string;
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
    INSERT INTO dl_request (
      status,
      platform,
      video_page_url,
      created,
      updated,
      mpd_or_m3u8_url,
      output_filename,
      preferred_quality_matcher,
      drm_token
    ) VALUES (
      $1, $2, $3, $4, $5, $6, $7, $8, $9
    ) RETURNING id
  `, [
    downloadRequest.status,
    downloadRequest.platform,
    downloadRequest.videoPageUrl,
    downloadRequest.created,
    downloadRequest.updated,
    downloadRequest.mpdOrM3u8Url,
    downloadRequest.outputFilename,
    downloadRequest.preferredQualityMatcher,
    downloadRequest.drmToken,
  ]);

  downloadRequest.id = result.rows[0].id;

  return downloadRequest;
}

export async function urlIsAlreadyPending(url: string): Promise<boolean> {
  const result = await getPool().query<{ count: number }>(`
    SELECT COUNT(*) FROM dl_request
    WHERE video_page_url = $1 AND status = $2
  `, [url, DLRequestStatus.PENDING]);

  return result.rows[0].count > 0;
}

export async function addManifestContentToDatabase(
  dlRequestId: number,
  content: string,
): Promise<DLRequestManifestContent> {
  const result = await getPool().query<{ id: number }>(`
    INSERT INTO dl_request_manifest_content (
      dl_request_id,
      content
    ) VALUES (
      $1, $2
    ) RETURNING id
  `, [dlRequestId, content]);

  return {
    id: result.rows[0].id,
    dl_request_id: dlRequestId,
    content,
  };
}
