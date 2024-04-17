import { pino } from 'pino';

let logger: pino.Logger = pino();
let loggerInitialized = false;

export function initLogging(): void {
  logger = pino({
    level: process.env.LOG_LEVEL || 'info',
    transport: {
      target: 'pino-pretty',
      options: {
        colorize: true,
        ignore: 'pid,hostname,tag',
        messageFormat: '[{tag}]: {msg}',
      },
    },
  });
  loggerInitialized = true;
}
export function getLogger(tag: string): typeof logger {
  if (!loggerInitialized) initLogging();
  return logger.child({ tag });
}
