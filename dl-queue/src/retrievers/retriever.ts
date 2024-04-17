import { Logger } from 'pino';

export abstract class Retriever {
  private cookieFilePath: string;
  protected logger: Logger;

  constructor(
    logger: Logger,
    cookieFileName: string,
  ) {
    this.logger = logger;
    this.cookieFilePath = process.env.COOKIE_FOLDER || './cookies' + '/' + cookieFileName.toLowerCase() + '.json';
  }

  public abstract retrieve(url: string): Promise<void>;
}
