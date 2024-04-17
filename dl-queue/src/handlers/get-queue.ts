import { Request, Response } from 'express';

export function getQueueHandler(
  req: Request,
  res: Response,
): void {
  res.json({ queue: [] });
}
