import { Request, Response } from 'express';
import { getPool } from '../utils/database';

export interface GetQueueRequestBody {
  list: string[] | undefined;
  count: string[] | undefined;
}

export async function getQueueHandler(
  req: Request,
  res: Response,
): Promise<void> {
  const contentType = req.get('Content-Type');
  if (contentType !== 'application/json') {
    res.status(400).send('Content-Type must be application/json');
    return;
  }

  const body = req.body as GetQueueRequestBody;

  if (body.list && !Array.isArray(body.list)) {
    res.status(400).json({ error: 'Invalid body' });
    return;
  }
  if (body.count && !Array.isArray(body.count)) {
    res.status(400).json({ error: 'Invalid body' });
    return;
  }

  let result: Record<string, unknown> = {};

  for (const key of new Set([ ...(body.list || []), ...(body.count || []) ])) {
    const res = await getPool().query(`
      SELECT
        id,
        status,
        platform,
        video_page_or_manifest_url,
        created,
        updated,
        output_filename,
        preferred_quality_matcher
      FROM dl.dl_request
      WHERE status = $1
    `, [key]);

    result = {
      ...result,
      ... (body.list?.includes(key)) && { [key]: res.rows },
      ... (body.count?.includes(key)) && { [`${key}_COUNT`]: res.rowCount },
    };
  }

  res.status(200).json(result);
}
