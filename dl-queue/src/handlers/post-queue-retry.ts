import { Request, Response } from 'express';
import { Logger } from 'pino';
import { getPool } from '../utils/database';
import { DLRequestStatus } from '../models/dl-request-status';

export interface PostQueueRetryRequestBody {
  id: number;
}

export async function postQueueRetryHandler(
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

  const body = req.body as PostQueueRetryRequestBody;
  const id = body?.id;
  if (!id || typeof id !== 'number') {
    res.status(400).send('Invalid or missing field: id (must be a number)');
    return;
  }

  // Fetch the current status of the request
  const currentResult = await getPool().query<{ status: string }>(`
    SELECT status FROM dl.dl_request WHERE id = $1
  `, [id]);

  if (currentResult.rows.length === 0) {
    res.status(404).send('Request not found');
    return;
  }

  const currentStatus = currentResult.rows[0].status;

  // Cannot retry if already PENDING or IN_PROGRESS
  if (currentStatus === DLRequestStatus.PENDING || currentStatus === DLRequestStatus.IN_PROGRESS) {
    res.status(400).send(`Cannot retry a request with status: ${currentStatus}`);
    return;
  }

  // Update the status to PENDING and set updated to current date
  const now = new Date();
  await getPool().query(`
    UPDATE dl.dl_request
    SET status = $1, updated = $2
    WHERE id = $3
  `, [DLRequestStatus.PENDING, now, id]);

  logger.child({ id }).info('Retrying request');

  res.status(200).json({ id, status: DLRequestStatus.PENDING, updated: now });
}
