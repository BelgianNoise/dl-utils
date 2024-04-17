import fs from 'fs';
import express from 'express';
import { config } from 'dotenv';
import bodyParser from 'body-parser';
import expressAsyncHandler from 'express-async-handler';
import { getQueueHandler } from './handlers/get-queue';
import { postQueueAddHandler } from './handlers/post-queue-add';
import { getLogger } from './utils/logging';

// Load environment variables from .env file
config();

const logger = getLogger('SERVER');

// Make sure all required environment variables are set
const requiredEnvVars: string[] = [];
requiredEnvVars.forEach((envVar) => {
  if (!process.env[envVar]) {
    logger.error(`Missing required environment variable: ${envVar}`);
    process.exit(1);
  }
});
// Make sure all required folder paths exist
const cookieFolder = process.env.COOKIE_FOLDER || './cookies';
const requiredPaths = [
  cookieFolder,
];
requiredPaths.forEach((path) => {
  if (!fs.existsSync(path)) {
    fs.mkdirSync(path);
  }
});

const app = express();
app.use(bodyParser.json());
const port = process.env.PORT || 3000;

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
