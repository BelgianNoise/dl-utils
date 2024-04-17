import crypto from 'crypto';
import { Cookie, Page } from 'puppeteer';
import { fromByteArray } from 'base64-js';
import { getLogger } from '../utils/logging';
import { DLRequest } from '../models/dl-request';
import { DLRequestStatus } from '../models/dl-request-status';
import { DLRequestPlatform } from '../models/dl-request-platform';
import { Retriever } from './retriever';

export class VRTMAXRetriever extends Retriever {
  constructor() {
    super(getLogger('VRTMAXRetriever'), 'vrt');
  }

  public async handle(
    url: string,
    includeManifestConetnt = false,
  ): Promise<{
    downloadRequest: DLRequest;
    manifestContent: string | undefined;
  }> {
    this.logger.debug(`Retrieving VRTMAX URL: ${url}`);

    const { streamId, name } = await this.getMetadata(url);
    this.logger.info(`Stream ID: ${streamId}`);
    this.logger.info(`Name: ${name}`);

    // Launch browser window and load in cookies if exist
    const playerInfo = await this.generatePlayerInfo();
    const cookies = await this.getAuthenticatedCookies();
    // get cookie named "vrtnu-site_profile_vt"
    const identityToken = cookies.find((cookie) => cookie.name === 'vrtnu-site_profile_vt')?.value;
    if (!identityToken) throw new Error('Could not find identity token (cookie: vrtnu-site_profile_vt)');
    const vrtPlayerToken = await this.getVRTPlayerToken(identityToken, playerInfo);
    const { drmToken, manifest } = await this.getManifestAndDrmToken(vrtPlayerToken, streamId);
    this.logger.info(`Manifest: ${manifest}`);
    this.logger.info(`DRM Token: ${drmToken}`);

    const dlRequest: DLRequest = {
      id: -1, // autoincrement
      status: DLRequestStatus.PENDING,
      platform: DLRequestPlatform.VRTMAX,
      videoPageUrl: url,
      created: new Date(),
      updated: new Date(),
      mpdOrM3u8Url: manifest,
      outputFilename: name,
      preferredQualityMatcher: undefined,
      drmToken: drmToken,
    };

    let manifestContent: string | undefined = undefined;
    if (includeManifestConetnt) {
      const manifestFileRequest = await fetch(manifest);
      if (manifestFileRequest.ok) {
        this.logger.debug('Manifest file request successful');
        manifestContent = await manifestFileRequest.text();
      } else {
        this.logger.debug('Manifest file request failed');
      }
    }

    return { downloadRequest: dlRequest, manifestContent };
  }

  private async getManifestAndDrmToken(
    vrtPlayerToken: string,
    streamId: string,
  ): Promise<{
    drmToken: string | undefined;
    manifest: string;
  }> {
    const streamRequestUrl = `https://media-services-public.vrt.be/media-aggregator/v2/media-items/${streamId}?` +
    `vrtPlayerToken=${vrtPlayerToken}` +
    '&client=vrtnu-web%40PROD';
    const streamRequest = await fetch(
      streamRequestUrl,
      {
        headers: {
          'user-agent': this.userAgent,
          'accept': '*/*',
          'accept-language': 'en',
        },
        body: null,
        method: 'GET',
      },
    );

    interface streamRequestResponse {
      aspectRatio: string;
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      drm: string | undefined;
      duration: number;
      posterImageUrl: string;
      shortDescription: string | null;
      skinType: string;
      title: string;
      targetUrls: {
        type: string;
        url: string;
      }[];
    }
    const streamData: streamRequestResponse = await streamRequest.json() as unknown as streamRequestResponse;
    const drmToken = streamData.drm;
    const manifest = streamData.targetUrls.find((target) => target.type.toLowerCase().includes('mpeg_dash'))?.url;
    if (!manifest) {
      this.logger.error('Could not find MPEG_DASH manifest URL in stream data');
      throw new Error('Could not find MPEG_DASH manifest URL in stream data');
    }

    return { drmToken, manifest };
  }

  private async getVRTPlayerToken(
    identityToken: string,
    playerInfo: string,
  ): Promise<string> {
    const tokenRequest = await fetch('https://media-services-public.vrt.be/vualto-video-aggregator-web/rest/external/v2/tokens', {
      headers: {
        'user-agent': this.userAgent,
        'accept': '*/*',
        'content-type': 'application/json',
      },
      body: JSON.stringify({
        identityToken: identityToken,
        playerInfo: playerInfo,
      }),
      method: 'POST',
    });
    const j: { vrtPlayerToken: string } = await tokenRequest.json() as unknown as { vrtPlayerToken: string };
    const vrtPlayerToken: string = j.vrtPlayerToken as unknown as string;

    return vrtPlayerToken;
  }

  // I don't think this is necessary anymore but let's keep it for now
  private async generatePlayerInfo(): Promise<string> {
    try {
      // Extract JWT key id and secret from player javascript
      const response = await fetch('https://player.vrt.be/vrtnu/js/main.js');
      const data = await response.text();
      const cryptRx = /atob\("(==[A-Za-z0-9+/]*)"/gm;
      const cryptData = data.match(cryptRx);
      if (!cryptData) throw new Error('');
      const kidSource = cryptData[1];
      const secretSource = cryptData[cryptData.length - 1];
      const kid = Buffer.from(kidSource.split('').reverse().join(''), 'base64').toString('utf-8');
      const secret = Buffer.from(secretSource.split('').reverse().join(''), 'base64').toString('utf-8');

      // Extract player version
      let playerVersion = '2.4.1';
      const pvRx = /playerVersion:"(\S*)"/;
      const match = data.match(pvRx);
      if (match) {
        playerVersion = match[1];
      }
      // Generate JWT
      const segments: string[] = [];
      const header: { [key: string]: string } = {
        alg: 'HS256',
        kid,
      };
      const payload: { [key: string]: unknown } = {
        exp: Math.floor(Date.now() / 1000) + 1000,
        platform: 'desktop',
        app: {
          type: 'browser',
          name: 'Firefox',
          version: '102.0',
        },
        device: 'undefined (undefined)',
        os: {
          name: 'Linux',
          version: 'x86_64',
        },
        player: {
          name: 'VRT web player',
          version: playerVersion,
        },
      };
      const jsonHeader = JSON.stringify(header);
      const jsonPayload = JSON.stringify(payload);
      segments.push(fromByteArray(Buffer.from(jsonHeader)).replace(/=/g, ''));
      segments.push(fromByteArray(Buffer.from(jsonPayload)).replace(/=/g, ''));
      const signingInput = segments.join('.');
      const signature = crypto.createHmac('sha256', Buffer.from(secret, 'utf-8')).update(signingInput).digest();
      segments.push(fromByteArray(signature).replace(/=/g, ''));
      const playerinfo = segments.join('.');

      this.logger.info('Player info: ' + playerinfo);
      return playerinfo;
    } catch (error) {
      this.logger.info('Could not extract JWT secret, download quality can possibly be limited to SD for older content');
      return '';
    }
  }

  private async getMetadata(url: string): Promise<{
    streamId: string;
    name: string;
  }> {
    const urlPath = new URL(url).pathname;

    const graphqlQuery = `
    query VideoPage($pageId: ID!) {
      page(id: $pageId) {
        ... on EpisodePage {
          episode {
            id
            title
            whatsonId
            brand
            brandLogos {
              type
              width
              height
              primary
              mono
            }
            logo
            durationValue
            durationSeconds
            onTimeRaw
            offTimeRaw
            ageRaw
            regionRaw
            announcementValue
            name
            permalink
            episodeNumberRaw
            episodeNumberValue
            subtitle
            richDescription {
              html
            }
            program {
              id
              link
              title
            }
            watchAction {
              streamId
              videoId
              episodeId
              avodUrl
              resumePoint
            }
          }
        }
      }
    }`;

    const body = {
      query: graphqlQuery,
      operationName: 'VideoPage',
      variables: {
        pageId: urlPath + '.model.json',
      },
    };

    const metadataRequest = await fetch('https://www.vrt.be/vrtnu-api/graphql/public/v1', {
      headers: {
        'user-agent': this.userAgent,
        'accept': 'application/graphql+json, application/json',
        'content-type': 'application/json',
        'x-vrt-client-name': 'WEB',
      },
      body: JSON.stringify(body),
      method: 'POST',
    });

    interface MetadataResponseBodt {
      data: {
        page: {
          episode: {
            name: string;
            watchAction: {
              streamId: string;
              videoId: string;
            },
          };
        };
      };
    }

    const metadata: MetadataResponseBodt = await metadataRequest.json() as unknown as MetadataResponseBodt;
    const name = metadata.data.page.episode.name;
    const streamId = metadata.data.page.episode.watchAction.streamId;

    return { streamId, name };
  }

  private async getAuthenticatedCookies(): Promise<Cookie[]> {
    const page = await this.getFreshPage();
    await this.loadCookies(page);

    await page.goto('https://www.vrt.be/vrtmax/', { waitUntil: ['networkidle2', 'load'] });
    await this.handleConsentPopup(page);

    try {
      // login check
      await page.hover('sso-login');
      // throw if 'admelden' button is not found
      await page.waitForSelector('pierce/li.menu-link a.afmelden', { timeout: 2000 });
      this.logger.debug('Already logged in!');

      const cookies = await page.cookies();
      // Save cookies again, some might be time sensitive
      await this.saveCookies(cookies);
      await this.closeBrowser();
      return cookies;
    } catch {
      this.logger.debug('Logging in...');
      await page.hover('sso-login');
      const loginButton = await page.waitForSelector('pierce/a.realAanmelden');
      // eslint-disable-next-line @typescript-eslint/no-explicit-any, @typescript-eslint/no-unsafe-return, @typescript-eslint/no-unsafe-call, @typescript-eslint/no-unsafe-member-access
      // await loginButton!.evaluate((el) => (el as any).click());
      await loginButton!.click();

      const email = process.env.AUTH_VRTMAX_EMAIL;
      if (!email) throw new Error('AUTH_VRTMAX_EMAIL not set');
      const emailInput = await page.waitForSelector('input#email-id-email');
      await emailInput!.type(email);
      const password = process.env.AUTH_VRTMAX_PASSWORD;
      if (!password) throw new Error('AUTH_VRTMAX_PASSWORD not set');
      const passwordInput = await page.waitForSelector('input#password-id-password');
      await passwordInput!.type(password);
      const submitButton = await page.waitForSelector('form button[type="submit"]');
      await submitButton!.click();

      await page.waitForNetworkIdle();
      await page.hover('sso-login');
      await page.waitForSelector('pierce/li.menu-link a.afmelden');
      this.logger.debug('Logged in successfully!');

      const cookies = await page.cookies();
      await this.saveCookies(cookies);

      await this.closeBrowser();
      return cookies;
    }
  }

  private async handleConsentPopup(page: Page) {
    try {
      this.logger.debug('Accepting cookies...');
      await page.waitForSelector('iframe[src*="consent"]', { timeout: 2000 });
      const frame = page.frames().find((frame) => frame.url().includes('consent'));
      const acceptButton = await frame!.waitForSelector('button[aria-label="Alles accepteren"]', { timeout: 2000 });
      await acceptButton!.click();
      this.logger.debug('Cookies accepted!');
    } catch {
      this.logger.debug('No cookies to accept, continuing...');
    }
  }
}
