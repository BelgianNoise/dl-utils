import { Scraper } from './scraper/scraper';
import { VRTScraper } from './scraper/vrt-scraper';

console.log('STARTING...');

async function main() {
  const scrapers: Scraper[] = [
    new VRTScraper(),
  ];

  for (const scraper of scrapers) {
    await scraper.init();
    await scraper.scrape();
    await scraper.destroy();
  }
}

void main().then(() => {
  console.log('DONE!');
});
