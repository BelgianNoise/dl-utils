import { Page } from 'puppeteer';
import { delay } from './delay';

export async function scrollToBottom(
  page: Page,
): Promise<Page> {
  // Scroll until no more results are loaded
  let previousHeight;
  // eslint-disable-next-line no-constant-condition
  while (true) {
    previousHeight = await page.evaluate('document.body.scrollHeight');
    await page.evaluate('window.scrollTo(0, document.body.scrollHeight)');
    await delay(300);
    const newHeight = await page.evaluate('document.body.scrollHeight');
    console.log('Scrolling', previousHeight, newHeight);
    if (newHeight === previousHeight) {
      break;
    }
  }

  return page;
}
