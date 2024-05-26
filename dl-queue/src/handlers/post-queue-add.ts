import { Request, Response } from 'express';
import { Logger } from 'pino';
import { DLRequest, addDownloadRequestToDatabase, urlIsAlreadyPending } from '../models/dl-request';
import { DLRequestPlatform } from '../models/dl-request-platform';
import { DLRequestStatus } from '../models/dl-request-status';
import { allowAllCORS } from '../utils/cors';

export interface PostQueueAddRequestBody {
  url: string;
  preferredQualityMatcher: string | undefined;
  outputFilename: string | undefined;
}

export async function postQueueAddHandler(
  req: Request,
  res: Response,
  logger: Logger,
): Promise<void> {
  allowAllCORS(req, res);

  // Must be Content-Type: application/json
  const contentType = req.get('Content-Type');
  if (contentType !== 'application/json') {
    res.status(400).send('Content-Type must be application/json');
    return;
  }
  // Parse JSON body (Typesafe)
  const body = req.body as PostQueueAddRequestBody;
  const url = body?.url;
  if (!url) {
    res.status(400).send(`Missing required field: url (${req.body})`);
    return;
  }
  try {
    new URL(url);
  } catch (e) {
    logger.debug(`invalid URL: ${url}`);
    res.status(400).send('Invalid URL');
    return;
  }

  logger.child({ url }).info('Received valid request');

  // Check if the database already contains a request that is pending for this URL
  if (await urlIsAlreadyPending(url)) {
    logger.info('Request is already pending');
    res.status(409).send('Request for this URL is already pending');
    return;
  }

  let downloadRequest: DLRequest = {
    id: -1,
    status: DLRequestStatus.PENDING,
    platform: DLRequestPlatform.UNKNOWN,
    videoPageOrManifestUrl: url,
    created: new Date(),
    updated: new Date(),
    outputFilename: body.outputFilename || undefined,
    preferredQualityMatcher: body.preferredQualityMatcher || undefined,
  };

  // Determine which function to call based on the hostname
  if (url.startsWith('https://www.vrt.be/vrtmax/')) {
    downloadRequest.platform = DLRequestPlatform.VRTMAX;
  } else if (url.startsWith('https://www.vtmgo.be/vtmgo')) {
    downloadRequest.platform = DLRequestPlatform.VTMGO;
  } else if (url.startsWith('https://www.goplay.be/')) {
    downloadRequest.platform = DLRequestPlatform.GOPLAY;
  } else if (url.startsWith('https://www.youtube.com/')) {
    downloadRequest.platform = DLRequestPlatform.YOUTUBE;
  } else if (url.includes('.m3u8') || url.includes('.mpd')) {
    downloadRequest.platform = DLRequestPlatform.GENERIC_MANIFEST;
  }

  // Write new download request to the database
  downloadRequest = await addDownloadRequestToDatabase(downloadRequest);
  logger.child({ url }).info('Added new download request to the database');

  res.status(201).json(downloadRequest);
}
