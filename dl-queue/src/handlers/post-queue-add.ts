import { Request, Response } from 'express';
import { Logger } from 'pino';
import { VRTMAXRetriever } from '../retrievers/VRTMAX-retriever';

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
  const body = req.body as { url: string };
  const url = body?.url;
  if (!url) {
    res.status(400).send(`Missing required field: url (${req.body})`);
    return;
  }
  try {
    new URL(url);
  } catch (e) {
    res.status(400).send('Invalid URL');
    return;
  }

  logger.info('Received request for URL: ' + url);

  // Determine which function to call based on the hostname
  if (url.startsWith('https://www.vrt.be/vrtmax/')) {
    await new VRTMAXRetriever().retrieve(url);
  } else {
    res.status(400).send('Unsupported URL');
    return;
  }

  res.status(201).send();
}
