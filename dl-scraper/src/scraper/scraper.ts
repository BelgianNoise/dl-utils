import fs from 'fs/promises';
import { Browser, CookieParam, Page, executablePath } from 'puppeteer';
import puppeteer from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';
import { Series } from '../models/Series';
import { Movie } from '../models/movie';

export interface ScraperOptions {
  browser?: Browser;
}

export abstract class Scraper {
  protected cookieFileLocation: string;
  protected userAgent: string = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 OPR/107.0.0.0';
  private browser: Browser | undefined = undefined;

  public constructor(cookieFileLocation?: string) {
    if (cookieFileLocation) {
      this.cookieFileLocation = cookieFileLocation;
    } else {
      this.cookieFileLocation = `cookies-${Date.now()}.json`;
    }
  }

  public async init(options?: ScraperOptions): Promise<void> {
    if (options?.browser) {
      this.browser = options.browser;
    } else {
      this.browser = await this.createDefaultBrowser();
    }
  }

  public async destroy(): Promise<void> {
    await this.getBrowser().close();
  }

  public async scrape(): Promise<void> {
    await this.getAllSeries();
    await this.getAllMovies();
  }

  private async createDefaultBrowser(): Promise<Browser> {
    puppeteer.use(StealthPlugin());
    // Launch the browser and open a new blank page
    const browser = await puppeteer.launch({
      headless: process.env.HEADLESS !== 'false',
      executablePath: executablePath(),
    });

    return browser;
  }

  protected getBrowser(): Browser {
    if (!this.browser) {
      throw new Error('Browser not initialized, did you call init() ?');
    }
    return this.browser;
  }

  protected async getCookies(): Promise<CookieParam[]> {
    try {
      const cookiesString = await fs.readFile(this.cookieFileLocation);
      // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
      const cookies: CookieParam[] = JSON.parse(cookiesString.toString());
      return cookies;
    } catch {
      console.log('no cookies found for', this.cookieFileLocation);
      return [];
    }
  }

  protected async getBlankPage(): Promise<Page> {
    const page = await this.getBrowser().newPage();
    await page.setExtraHTTPHeaders({
      'Accept-Language': 'nl-BE,nl',
    });

    try {
      const cookies = await this.getCookies();
      await page.setCookie(...cookies);
    } catch {
      console.log('no cookies found for', this.cookieFileLocation);
    }

    await page.setViewport({width: 1280, height: 720});
    await page.setUserAgent('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 OPR/105.0.0.0');

    return page;
  }

  protected async saveCookies(page: Page): Promise<void> {
    console.log('Saving cookies...');
    const cookies = await page.cookies();
    await fs.writeFile(
      this.cookieFileLocation,
      JSON.stringify(cookies, null, 2),
    );
    console.log('Cookies saved!');
  }

  protected getAllHeadersForFetch(): Record<string, string> {
    return {
      'User-Agent': this.userAgent,
    };
  }

  protected abstract handleCookiePopup(page: Page): Promise<void>;
  public abstract getAllSeries(): Promise<Series[]>;
  public abstract getAllMovies(): Promise<Movie[]>;
}
