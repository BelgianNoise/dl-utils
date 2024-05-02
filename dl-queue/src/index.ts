import express from 'express';
import { config } from 'dotenv';
import bodyParser from 'body-parser';
import expressAsyncHandler from 'express-async-handler';
import { getQueueHandler } from './handlers/get-queue';
import { postQueueAddHandler } from './handlers/post-queue-add';
import { getLogger } from './utils/logging';
import { testDatabaseConnection } from './utils/database';
import { allowAllCORS } from './utils/cors';

// Load environment variables from .env file
config();

const logger = getLogger('SERVER');

// Make sure all required environment variables are set
const requiredEnvVars: string[] = [
  'POSTGRES_USERNAME',
  'POSTGRES_PASSWORD',
  'POSTGRES_HOST',
  'POSTGRES_PORT',
  'POSTGRES_DATABASE',
  'AUTH_SECRET',
];
requiredEnvVars.forEach((envVar) => {
  if (!process.env[envVar]) {
    logger.error(`Missing required environment variable: ${envVar}`);
    process.exit(1);
  }
});

// Validate database connection
testDatabaseConnection().then(() => {
  logger.info('Successfully connected to database');
}).catch(() => {
  logger.error('Failed to connect to database, shutting down server');
  process.exit(1);
});

const app = express();
app.use(bodyParser.json());
const port = process.env.PORT || 3000;

app.use((req, res, next) => {
  if (req.method === 'OPTIONS') {
    allowAllCORS(req, res);
    res.sendStatus(200);
  } else {
    next();
  }
});

// Authentication middleware
app.use((req, res, next) => {
  const authHeader = req.headers.authorization;
  if (!authHeader) {
    logger.warn('Missing Authorization header');
    res.sendStatus(401);
  } else if (authHeader !== process.env.AUTH_SECRET) {
    logger.warn('Invalid Authorization header');
    res.sendStatus(401);
  } else {
    next();
  }
});

app.get('/queue', (req, res) => {
  logger.info('GET /queue');
  void getQueueHandler(req, res);
});

app.post('/queue/add', expressAsyncHandler( async(req, res) => {
  logger.info('POST /queue/add');
  await postQueueAddHandler(req, res, logger);
}));

logger.info(`Starting server on port ${port} ...`);
app.listen(port, () => {
  logger.info(`Server started on port ${port}!`);
});
