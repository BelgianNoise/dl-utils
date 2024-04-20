import fs from 'fs/promises';
import { CookieParam, Page, executablePath } from 'puppeteer';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';
import puppeteer from 'puppeteer-extra';

const link = 'https://www.vtmgo.be/vtmgo/afspelen/adf9caa7-ee22-4608-a719-efef8c5ad27f';

console.log('STARTING...');

async function checkCookiePopup(page: Page) {
  try {
    console.log('Accepting cookies...');
    const button = await page.waitForSelector(
      'pierce/#pg-accept-btn',
      { timeout: 2000 },
    );
    if (!button) throw new Error('Button not found!');
    await button.click();
    console.log('Cookies accepted!');
  } catch {
    console.log('No cookies to accept, continuing...');
  }
}

async function handleAuth(page: Page) {
  try {
    // login check
    await page.waitForSelector(
      'a[href="https://www.vtmgo.be/vtmgo/mijn-lijst"]',
      { timeout: 2000 },
    );
    console.log('Already logged in!');
  } catch {
    console.log('Logging in...');
    const loginButton = await page.waitForSelector('a.btn[js-module="loginRedirect"]');
    if (!loginButton) {
      console.error('Login button not found!');
      return;
    }
    await loginButton.click();

    const usernameInput = await page.waitForSelector('input#username');
    if (!usernameInput) {
      console.error('Username input not found!');
      return;
    }
    await usernameInput.type('xxx');
    const submitButton = await page.waitForSelector('form button[type="submit"]');
    if (!submitButton) {
      console.error('Submit button not found!');
      return;
    }
    await submitButton.click();
    const passwordInput = await page.waitForSelector('input#password');
    if (!passwordInput) {
      console.error('Password input not found!');
      return;
    }
    await passwordInput.type('xxx');
    const submitButton2 = await page.waitForSelector('form button[type="submit"]');
    if (!submitButton2) {
      console.error('Submit button 2 not found!');
      return;
    }
    await submitButton2.click();

    await page.waitForSelector('a[href="https://www.vtmgo.be/vtmgo/mijn-lijst"]');
    console.log('Logged in successfully!');
  }
}

async function main() {
  puppeteer.use(StealthPlugin());
  // listen for all requests to https://videoplayer-service.dpgmedia.net/config/episodes/
  const browser = await puppeteer.launch({
    headless: false,
    executablePath: executablePath(),
  });
  const page = await browser.newPage();
  await page.setExtraHTTPHeaders({
    'Accept-Language': 'nl-BE,nl',
  });
  console.log('reading cookies...');
  try {
    const cookiesBuffer = await fs.readFile('./cookies/vtm.json');
    const cookies = JSON.parse(cookiesBuffer.toString()) as CookieParam[];
    await page.setCookie(...cookies);
    console.log('using cookies');
  } catch {
    console.log('no cookies found');
  }
  await page.setViewport({width: 1920, height: 1080});
  await page.setUserAgent('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 OPR/105.0.0.0');
  await page.goto(
    'https://www.vtmgo.be/vtmgo',
    { waitUntil: ['networkidle2', 'load'] },
  );

  console.log('=== PAGE LOADED');

  await checkCookiePopup(page);
  await handleAuth(page);

  console.log('=== READY');

  console.log(`Link: ${link}`);
  const splitLink = link.split('/');
  const assetId = splitLink[splitLink.length - 1];
  console.log(`Asset ID: ${assetId}`);

  const cencResponse = page.waitForResponse(
    (res) => {
      if (!res.url().startsWith('https://lic.drmtoday.com/license-proxy-widevine/cenc')) return false;
      console.log('CENC response:', res.url(), res.status());
      if (res.status() === 204) return false;
      if (!res.headers()['X-Dt-Client-Info']) return false;
      return true;
    },
  );
  const m3u8Response = page.waitForResponse(
    (res) =>
      res.url().startsWith('https://videoplayer-service.dpgmedia.net/config/episodes/')
      && res.url().includes(assetId)
      && res.status() !== 204, // Dang I hate OPTIONS requests
  );
  await page.goto(link);
  const m3u8Res = await m3u8Response;
  console.log('M3U8 response:', m3u8Res.url());
  console.log('M3U8 status:', m3u8Res.status());
  // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
  const m3u8Data: { video: { streams: {url: string, drm: {'com.widevine.alpha': {licenseUrl: string}}}[] } } = await m3u8Res.json();
  const stream = m3u8Data.video.streams[1];
  const m3u8Url = stream.url;
  const licenseUrl = stream.drm['com.widevine.alpha'].licenseUrl;
  console.log('M3U8 URL:', m3u8Url);
  console.log('License URL:', licenseUrl);

  const cencRes = await cencResponse;
  // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
  const cencData: { supported_tracks: {key_id: string}[]} = await cencRes.json();
  console.log('CENC DATA:', JSON.stringify(cencData, null, 2));

  // Saving cookies in the end to make sure we have the latest ones
  console.log('Saving cookies...');
  const cookies = await page.cookies();
  await fs.writeFile('./cookies/vtm.json', JSON.stringify(cookies, null, 2));
  console.log('Cookies saved!');

  await browser.close();
}

void main().then(() => {
  console.log('DONE!');
});
