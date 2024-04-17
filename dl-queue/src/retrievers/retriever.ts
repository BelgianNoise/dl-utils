import fs from 'fs/promises';
import { Logger } from 'pino';
import { Browser, Cookie, Page, executablePath } from 'puppeteer';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';
import puppeteer from 'puppeteer-extra';
import { DLRequest } from '../models/dl-request';

export abstract class Retriever {
  private cookieFilePath: string;
  protected logger: Logger;
  protected userAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 OPR/107.0.0.0';
  protected browser: Browser | undefined;

  constructor(
    logger: Logger,
    cookieFileName: string,
  ) {
    this.logger = logger;
    this.cookieFilePath = (process.env.COOKIE_FOLDER || './cookies') + '/' + cookieFileName.toLowerCase() + '.json';
  }

  public abstract handle(
    url: string,
    includeManifestConetnt?: boolean,
  ): Promise<{
    downloadRequest: DLRequest;
    manifestContent: string | undefined;
  }>;

  private async initBrowser(): Promise<Browser> {
    this.logger.debug('Initializing browser');
    puppeteer.use(StealthPlugin());
    const browser = await puppeteer.launch({
      executablePath: executablePath(),
      headless: process.env.HEADLESS !== 'false',
    });
    this.browser = browser;
    return this.browser;
  }

  protected async getBrowser(): Promise<Browser> {
    if (!this.browser) {
      return await this.initBrowser();
    } else {
      return this.browser;
    }
  }

  protected async saveCookies(cookies: Cookie[]): Promise<void> {
    this.logger.debug(`Saving cookies to ${this.cookieFilePath}`);
    await fs.writeFile(this.cookieFilePath, JSON.stringify(cookies, null, 2));
    this.logger.debug('Cookies saved');
  }

  protected async saveCookiesFromPage(page: Page): Promise<void> {
    const cookies = await page.cookies();
    await this.saveCookies(cookies);
  }

  protected async getCookies(): Promise<Cookie[]> {
    return JSON.parse(await fs.readFile(this.cookieFilePath, 'utf-8')) as Cookie[];
  }

  protected async loadCookies(page: Page): Promise<void> {
    this.logger.debug('Loading cookies');
    try {
      const cookies = await this.getCookies();
      await page.setCookie(...cookies);
    } catch {
      this.logger.debug('Failed to load cookies');
    }
  }

  protected async getFreshPage(): Promise<Page> {
    const browser = await this.getBrowser();
    const page = await browser.newPage();
    await page.setExtraHTTPHeaders({
      'Accept-Language': 'nl-BE,nl',
    });
    await page.setUserAgent(this.userAgent);
    // await page.setViewport({ width: 1920, height: 1080 });

    return page;
  }

  protected async closeBrowser(): Promise<void> {
    if (this.browser) {
      this.logger.debug('Closing browser');
      await this.browser.close();
      this.browser = undefined;
    }
  }
  public async teardown(): Promise<void> {
    await this.closeBrowser();
  }
}
