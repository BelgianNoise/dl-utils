import { Request, Response } from 'express';
import { Logger } from 'pino';
import { VRTMAXRetriever } from '../retrievers/VRTMAX-retriever';
import { Retriever } from '../retrievers/retriever';
import { DLRequest, DLRequestManifestContent, addDownloadRequestToDatabase, addManifestContentToDatabase, urlIsAlreadyPending } from '../models/dl-request';

export interface PostQueueAddRequestBody {
  url: string;
  preferredQualityMatcher: string | undefined;
}

export async function postQueueAddHandler(
  req: Request,
  res: Response,
  logger: Logger,
): Promise<void> {
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

  logger.info(`Received request for URL: ${url}`);

  // Check if the database already contains a request that is pending for this URL
  if (await urlIsAlreadyPending(url)) {
    logger.info('Request is already pending');
    res.status(409).send('Request for this URL is already pending');
    return;
  }

  let retriever: Retriever;

  // Determine which function to call based on the hostname
  if (url.startsWith('https://www.vrt.be/vrtmax/')) {
    retriever = new VRTMAXRetriever();
  } else {
    res.status(400).send('Unsupported URL');
    return;
  }

  let downloadRequest: DLRequest;
  let manifestContent: string | undefined;
  try {
    ({ downloadRequest, manifestContent } = await retriever.handle(url, true));
  } catch (e: unknown) {
    await retriever.teardown();
    logger.error(e);
    res.status(500).send('Internal server error');
    return;
  } finally {
    await retriever.teardown();
  }

  // Fill preferredQualityMatcher
  if (body.preferredQualityMatcher) {
    downloadRequest.preferredQualityMatcher = body.preferredQualityMatcher;
  }

  // Write new download request to the database
  downloadRequest = await addDownloadRequestToDatabase(downloadRequest);
  logger.info(`Added new download request to the database: ${downloadRequest.id}`);

  if (manifestContent) {
    // Write new manifest content to the database
    const dlManifestContent = await addManifestContentToDatabase(downloadRequest.id, manifestContent);
    logger.info(`Added new manifest content to the database: ${dlManifestContent.id}`);
  }

  res.status(201).send();
}
