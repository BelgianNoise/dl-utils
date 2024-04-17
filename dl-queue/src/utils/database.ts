import { Pool, PoolClient } from 'pg';
import { getLogger } from './logging';

let pool: Pool;

export function getPool(): Pool {
  if (!pool) {
    pool = new Pool({
      user: process.env.POSTGRES_USERNAME,
      password: process.env.POSTGRES_PASSWORD,
      host: process.env.POSTGRES_HOST,
      port: parseInt(process.env.POSTGRES_PORT || '5432'), // Default only required for TypeScript
      database: process.env.POSTGRES_DATABASE,
      max: 3,
      idleTimeoutMillis: 120000,
    });
    getLogger('DATABASE').info('Created new database connection pool');
  }

  return pool;
}

export function getPoolClient(): Promise<PoolClient> {
  return getPool().connect();
}

export async function testDatabaseConnection(): Promise<void> {
  await getPool().query('SELECT id FROM dl_request LIMIT 1');
}