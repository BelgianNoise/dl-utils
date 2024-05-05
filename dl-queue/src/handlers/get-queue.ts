import { Request, Response } from 'express';
import { getPool } from '../utils/database';

export interface GetQueueRequestBody {
  list: string[] | undefined;
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

  let result: Record<string, unknown> = {};

  for (const key of new Set([ ...(body.list || []) ])) {
    const res = await getPool().query(`
      SELECT
        id,
        status,
        platform,
        video_page_or_manifest_url AS "videoPageOrManifestUrl",
        created,
        updated,
        output_filename AS "outputFilename",
        preferred_quality_matcher AS "preferredQualityMatcher"
      FROM dl.dl_request
      WHERE status = $1
      ORDER BY updated DESC
      LIMIT 100
    `, [key]);

    result = {
      ...result,
      [key]: res.rows,
    };
  }

  res.status(200).json(result);
}
