import { Page } from 'puppeteer';
import { delay } from '../utils/delay';
import { Movie } from '../models/movie';
import { Episode, Serie, Season } from '../models/Serie';
import { Language } from '../models/language';
import { scrollToBottom } from '../utils/scroll-to-bottom';
import { Scraper } from './scraper';

export class VRTScraper extends Scraper {
  public constructor() {
    super('./cookies/vrt.json');
  }

  protected async handleCookiePopup(
    page: Page,
  ): Promise<void> {
    if (this.checkForCookiePopup === false) return;

    const cookies = await page.cookies();
    // return if cookie "consentDate" is set
    if (cookies.find((cookie) => cookie.name === 'consentDate')) {
      this.checkForCookiePopup = false;
      return;
    }

    try {
      console.log('Checking for cookie popup');
      const frame = await page.waitForSelector(
        'iframe[title="SP Consent Message"]',
        { timeout: 500 },
      );
      if (!frame) throw new Error();
      const frameContent = await frame.contentFrame();
      if (!frameContent) throw new Error();
      const button = await frameContent.waitForSelector('button[aria-label="Alles weigeren"]');
      if (!button) throw new Error();
      await button.click();
      await delay(2000);
    } catch (e) {
      console.log('No cookie popup found');
    }
  }

  public async getAllSeries(): Promise<Serie[]> {
    const page = await this.getBlankPage();

    await page.goto('https://www.vrt.be/vrtmax/zoeken/?facets=%5B%7B"name"%3A"contenttype"%2C"values"%3A%5B"series"%5D%7D%5D');
    await page.waitForSelector('section[aria-label="Kijk"] ul li a');
    // await scrollToBottom(page);
    await delay(200);

    const seriesList: Serie[] = [];

    // Select all items: section[aria-label="Kijk"] ul li
    const lis = await page.$$('section[aria-label="Kijk"] ul li');
    console.log('Found', lis.length, 'series');
    for (const li of lis) {
      // Get hyperlink
      const a = await li.$('a');
      if (!a) {
        console.error('No <a> found');
        continue;
      }
      const href = await page.evaluate((a) => a.href, a);
      if (!href) {
        console.error('No href found');
        continue;
      }

      // Get title
      const h3 = await li.$('h3');
      if (!h3) {
        console.error('No <h3> found');
        continue;
      }
      const title = await page.evaluate((h3) => h3.textContent, h3);
      if (!title) {
        console.error('No title found');
        continue;
      }

      // Get description
      const p = await li.$('p');
      if (!p) {
        console.error('No <p> found');
        continue;
      }
      const description = await page.evaluate((p) => p.textContent, p);
      if (!description) {
        console.error('No description found');
        continue;
      }

      // Get poster
      const img = await li.$('img');
      if (!img) {
        console.error('No <img> found');
        continue;
      }
      const poster = await page.evaluate((img) => img.src, img);

      // Init default serie object
      const serie: Serie = {
        hyperlink: href,
        title: title,
        poster: poster,
        description: description,
        language: Language.UNKNOWN,
        seasons: new Map<string, Season>(),
      };

      seriesList.push(serie);
    }

    for (const serie of seriesList) {
      // Get seasons information
      console.log('Visiting', serie.hyperlink);
      await page.goto(serie.hyperlink);
      await scrollToBottom(page);

      // Wait till share button is visible
      await page.waitForSelector('button[aria-label="Toon de opties om deze pagina te delen"]');
      await this.handleCookiePopup(page);

      // find the season dropdown
      const seasons = await page.$$('select option');
      if (seasons.length === 0) {
        // There is no season dropdown, so there is only 1 season
        console.log('No seasons found, assuming 1 season');
        const episodes = await page.$$('ul li[data-content-type="episode"]');
        // Handle every episode as if it could be in its own season
        for (const episode of episodes) {
          // Get all div span.screenreader
          const spans = await episode.$$('div span.screenreader');
          // 2 spans are expected: the first one is the season, the second one is the episode
          if (spans.length !== 2) {
            console.error('Expected 2 spans, got', spans.length);
            continue;
          }
          const seasonTitle = await page.evaluate((span) => span.textContent, spans[0]);
          if (!seasonTitle) {
            console.error('No season title found');
            continue;
          }

          let season: Season | undefined = serie.seasons.get(seasonTitle);
          if (!season) {
            season = {
              title: seasonTitle,
              poster: serie.poster,
              episodes: [],
            };
          }

          const episodeNumberTitle = await page.evaluate((span) => span.textContent, spans[1]);
          if (!episodeNumberTitle) {
            console.error('No episode number title found');
            continue;
          }
          const episodeNumber = parseInt(episodeNumberTitle.split(' ')[1]);
          if (isNaN(episodeNumber)) {
            console.error('Could not parse episode number');
            continue;
          }
          const episodeTitleH3 = await episode.$('h3');
          if (!episodeTitleH3) {
            console.error('No episode title <h3> found');
            continue;
          }
          const episodeTitle = await page.evaluate((h3) => h3.textContent, episodeTitleH3);
          if (!episodeTitle) {
            console.error('No episode title found');
            continue;
          }

          // Episode thumbnail is optional
          let episodeThumbnail = '';
          const episodeThumbnailImg = await episode.$('img');
          if (episodeThumbnailImg) {
            episodeThumbnail = await page.evaluate((img) => img.src, episodeThumbnailImg);
          }

          // Episode hyperlink is optional
          let episodeHyperLink = '';
          const hyperlinkA = await episode.$('a');
          if (hyperlinkA) {
            const hyperlink = await page.evaluate((a) => a.href, hyperlinkA);
            episodeHyperLink = hyperlink;
          }

          // Episode description is optional
          let episodeDescription = '';
          const episodeDescriptionP = await episode.$('p');
          if (episodeDescriptionP) {
            const desc = await page.evaluate((p) => p.textContent, episodeDescriptionP);
            if (desc !== null) {
              episodeDescription = desc;
            }
          }

          const episodeObject: Episode = {
            title: episodeTitle,
            number: episodeNumber,
            description: episodeDescription,
            durationSeconds: 0,
            hyperlink: episodeHyperLink,
            thumbnail: episodeThumbnail,
          };

          // Add episode to season
          season.episodes.push(episodeObject);
          // Add season (back) to serie
          serie.seasons.set(seasonTitle, season);
        }
      } else {
        console.log('Found', seasons.length, 'seasons');
        // TODO: Implement multiple seasons
      }

      // Wait 1 second
      await delay(1000);
    }

    for (const serie of seriesList) {
      console.log(serie);
      if (serie.title.includes('dijken')) {
        for (const [seasonTitle, season] of serie.seasons) {
          console.log(seasonTitle, season);
        }
      }
    }
    await this.saveCookies(page);

    return seriesList;
  }

  public async getAllMovies(): Promise<Movie[]> {
    console.log('Getting all movies');
    await delay(1000);
    return [];
  }
}
