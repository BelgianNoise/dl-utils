import { Page } from 'puppeteer';
import { delay } from '../utils/delay';
import { Movie } from '../models/movie';
import { Episode, Series, Season } from '../models/Series';
import { Language } from '../models/language';
import { scrollToBottom } from '../utils/scroll-to-bottom';
import { MoreSeasonsResponse, ProgramResponse, SearchResultResponse, VRT_COMPONENT, VRT_NODE, getProgramsQuery, getSingleProgramQuery } from '../utils/vrt-scraper-utils';
import { Scraper } from './scraper';

export class VRTScraper extends Scraper {
  private bearerToken = '';

  public constructor() {
    super('./cookies/vrt.json');
  }

  protected async handleCookiePopup(
    page: Page,
  ): Promise<void> {
    try {
      console.log('Checking for cookie popup');
      const frame = await page.waitForSelector(
        'iframe[title="SP Consent Message"]',
        { timeout: 2000 },
      );
      if (!frame) throw new Error();
      const frameContent = await frame.contentFrame();
      if (!frameContent) throw new Error();
      const button = await frameContent.waitForSelector('button[aria-label="Accept All"]');
      if (!button) throw new Error();
      await button.click();
      await delay(2000);
    } catch (e) {
      console.log('No cookie popup found');
    }
  }

  protected async handleLogin(
    page: Page,
  ): Promise<Page> {
    try {
      await page.hover('sso-login');
      await page.waitForSelector('pierce/li.menu-link a.afmelden', { timeout: 2000 });
      console.log('Already logged in');
    } catch {
      console.log('Logging in ...');
      const loginButton = await page.waitForSelector('pierce/a.realAanmelden');
      if (!loginButton) throw new Error('No login button found');
      await loginButton.click();

      if (!process.env.AUTH_VRTMAX_EMAIL) throw new Error('AUTH_VRTMAX_EMAIL env variable not set');
      if (!process.env.AUTH_VRTMAX_PASSWORD) throw new Error('AUTH_VRTMAX_PASSWORD env variable not set');

      const emailInput = await page.waitForSelector('input#email-id-email');
      if (!emailInput) throw new Error('No email input found');
      await emailInput.type(process.env.AUTH_VRTMAX_EMAIL);
      const passwordInput = await page.waitForSelector('input#password-id-password');
      if (!passwordInput) throw new Error('No password input found');
      await passwordInput.type(process.env.AUTH_VRTMAX_PASSWORD);
      const submitButton = await page.waitForSelector('form button[type="submit"]');
      if (!submitButton) throw new Error('No submit button found');
      await submitButton.click();
      await page.waitForNetworkIdle();

      await page.waitForSelector('pierce/li.menu-link a.afmelden');
      console.log('Logged in successfully');
    } finally {
      await this.saveCookies(page);
      const cookies = await page.cookies();
      this.bearerToken = cookies.find((cookie) => cookie.name === 'vrtnu-site_profile_at')?.value || '';
      console.log('Token:', this.bearerToken);
    }
    return page;
  }

  protected getAllHeadersForFetch(): Record<string, string> {
    return {
      'accept': 'application/graphql+json, application/json',
      'accept-encoding': 'gzip, deflate, br',
      'content-type': 'application/json',
      'authorization': `Bearer ${this.bearerToken}`,
      'user-agent': this.userAgent,
      'x-vrt-client-name': 'WEB',
      'x-vrt-client-version': '1.5.1',
      'x-vrt-zone': 'default',
    };
  }

  public async getAllSeries(): Promise<Series[]> {
    // refresh cookies
    const page = await this.getBlankPage();
    await page.goto('https://www.vrt.be/vrtmax/');
    await page.waitForNetworkIdle();
    await this.handleCookiePopup(page);
    await this.handleLogin(page);

    const listIdObject = {
      queryString: '',
      facets: [
        {
          name: 'contenttype',
          values: ['series'],
        },
        {
          name: 'entitytype',
          values: ['video-program'],
        },
      ],
      resultType: 'watch',
    };

    // Get a list of all the available series
    const seriesList: Series[] = [];
    let lastCursor = '';

    // eslint-disable-next-line no-constant-condition
    while (true) {
      const res = await fetch('https://www.vrt.be/vrtnu-api/graphql/v1', {
        headers: this.getAllHeadersForFetch(),
        body: JSON.stringify({
          query: getProgramsQuery,
          operationName: 'PaginatedTileListPage',
          variables: {
            listId: 'uisearch:searchdata@' + Buffer.from(JSON.stringify(listIdObject)).toString('base64'),
            ... (lastCursor) && { after: lastCursor },
          },
        }),
        method: 'POST',
      });

      // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
      const json: SearchResultResponse = await res.json();

      console.log('Processing', json.data.list.paginatedItems.edges.length, 'edges');
      for (const edge of json.data.list.paginatedItems.edges) {
        const series: Series = {
          platformSpecificId: edge.node.objectId,
          title: edge.node.title,
          description: edge.node.description,
          language: Language.UNKNOWN,
          poster: edge.node.image.templateUrl,
          hyperlink: new URL(edge.node.link, 'https://www.vrt.be').toString(),
          seasons: new Map<string, Season>(),
        };
        seriesList.push(series);
      }

      console.log('Found', seriesList.length, 'series so far');
      const pageInfo = json.data.list.paginatedItems.pageInfo;
      lastCursor = pageInfo.endCursor;
      if (pageInfo.hasNextPage === false) break;
    }

    console.log('Found', seriesList.length, 'series');
    seriesList.splice(4);

    // Retrieve all seasons and episodes
    for (const series of seriesList) {
      const res = await fetch('https://www.vrt.be/vrtnu-api/graphql/v1', {
        headers: this.getAllHeadersForFetch(),
        body: JSON.stringify({
          query: getSingleProgramQuery,
          operationName: 'VideoProgramPage',
          variables: {
            pageId: `${new URL(series.hyperlink).pathname}.model.json`,
          },
        }),
        method: 'POST',
      });

      // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
      const json: ProgramResponse = await res.json();
      // Find all 'EpisodeTile' VRT_NODE objects
      const episodeNodes: VRT_NODE[] = [];
      for (const comp of json.data.page.components) {
        const nodes = await this.getAllEpisodeTileNodes(comp);
        episodeNodes.push(...nodes);
      }
      console.log('Found', episodeNodes.length, 'EpisodeTile nodes for', series.title);

      for (const node of episodeNodes) {
        if (node.primaryMeta.length < 2) {
          console.error('Not enough primaryMeta found for', node.title);
          continue;
        }
        const seasonMeta = node.primaryMeta[0];
        const episodeMeta = node.primaryMeta[1];
        const seasonTitle = seasonMeta.value;
        if (!seasonTitle) continue;
        const episodeNumberString = episodeMeta.value;
        if (!episodeNumberString) continue;
        const episodeNumberMatches = episodeNumberString.match(/(\d+)/);
        if (!episodeNumberMatches) {
          console.error('No episode number found for', node.title);
          continue;
        }
        const episodeNumber = parseInt(episodeNumberMatches[0]);

        const episode: Episode = {
          platformSpecificId: node.objectId,
          title: node.title,
          number: episodeNumber,
          description: node.description,
          durationSeconds: 0,
          hyperlink: new URL(node.playAction.pageUrl, 'https://www.vrt.be').toString(),
          thumbnail: node.image.templateUrl,
        };

        if (!series.seasons.has(seasonTitle)) {
          series.seasons.set(seasonTitle, {
            title: seasonTitle,
            poster: series.poster,
            episodes: [],
            platformSpecificId: undefined,
          });
          console.log('Added season', seasonTitle, 'to', series.title);
        }
        series.seasons.get(seasonTitle)?.episodes.push(episode);
      }
    }

    console.log(seriesList);
    console.log(seriesList[0].seasons.get('Seizoen 1'));
    return seriesList;
  }

  public async getAllMovies(): Promise<Movie[]> {
    console.log('Getting all movies');
    await delay(1000);
    return [];
  }

  private async getAllEpisodeTileNodes(comp: VRT_COMPONENT): Promise<VRT_NODE[]> {
    const nodeList: VRT_NODE[] = [];

    if (comp.__typename === 'PaginatedTileList') {
      if (comp.paginatedItems) {
        for (const edge of comp.paginatedItems.edges) {
          if (edge.node.__typename === 'EpisodeTile') {
            nodeList.push(edge.node);
          }
        }
      } else {
        console.log('No paginatedItems found in', comp.__typename);
      }
    } else if (comp.__typename === 'LazyTileList') {
      // This means there is a season for which the data is not loaded in yet
      // use the 'listId' to fetch the data
      console.log('LazyTileList found in, fetching data for', comp.listId);

      const res = await fetch('https://www.vrt.be/vrtnu-api/graphql/v1', {
        headers: this.getAllHeadersForFetch(),
        body: '{"query":"query ProgramSeasonEpisodeList($listId: ID!, $sort: SortInput, $lazyItemCount: Int = 20, $after: ID, $before: ID) {\\n  list(listId: $listId, sort: $sort) {\\n    __typename\\n    ... on PaginatedTileList {\\n      ...paginatedTileListFragment\\n      __typename\\n    }\\n    ... on StaticTileList {\\n      ...staticTileListFragment\\n      __typename\\n    }\\n  }\\n}\\nfragment staticTileListFragment on StaticTileList {\\n  __typename\\n  objectId\\n  listId\\n  title\\n  description\\n  tileContentType\\n  tileOrientation\\n  displayType\\n  expires\\n  tileVariant\\n  sort {\\n    icon\\n    order\\n    title\\n    __typename\\n  }\\n  actionItems {\\n    ...actionItemFragment\\n    __typename\\n  }\\n  banner {\\n    actionItems {\\n      ...actionItemFragment\\n      __typename\\n    }\\n    description\\n    image {\\n      ...imageFragment\\n      __typename\\n    }\\n    compactLayout\\n    backgroundColor\\n    textTheme\\n    title\\n    titleArt {\\n      objectId\\n      templateUrl\\n      __typename\\n    }\\n    __typename\\n  }\\n  bannerSize\\n  items {\\n    ...tileFragment\\n    __typename\\n  }\\n  ... on IComponent {\\n    ...componentTrackingDataFragment\\n    __typename\\n  }\\n}\\nfragment actionItemFragment on ActionItem {\\n  __typename\\n  objectId\\n  accessibilityLabel\\n  action {\\n    ...actionFragment\\n    __typename\\n  }\\n  active\\n  icon\\n  iconPosition\\n  icons {\\n    __typename\\n    position\\n    ... on DesignSystemIcon {\\n      value {\\n        name\\n        __typename\\n      }\\n      __typename\\n    }\\n  }\\n  mode\\n  objectId\\n  title\\n}\\nfragment actionFragment on Action {\\n  __typename\\n  ... on FavoriteAction {\\n    favorite\\n    id\\n    programUrl\\n    programWhatsonId\\n    title\\n    __typename\\n  }\\n  ... on ListDeleteAction {\\n    listName\\n    id\\n    listId\\n    title\\n    __typename\\n  }\\n  ... on ListTileDeletedAction {\\n    listName\\n    id\\n    listId\\n    __typename\\n  }\\n  ... on PodcastEpisodeListenAction {\\n    id: audioId\\n    podcastEpisodeLink\\n    resumePointProgress\\n    resumePointTotal\\n    completed\\n    __typename\\n  }\\n  ... on EpisodeWatchAction {\\n    id: videoId\\n    videoUrl\\n    resumePointProgress\\n    resumePointTotal\\n    completed\\n    __typename\\n  }\\n  ... on LinkAction {\\n    id: linkId\\n    linkId\\n    link\\n    linkType\\n    openExternally\\n    passUserIdentity\\n    linkTokens {\\n      __typename\\n      placeholder\\n      value\\n    }\\n    __typename\\n  }\\n  ... on ShareAction {\\n    title\\n    url\\n    __typename\\n  }\\n  ... on SwitchTabAction {\\n    referencedTabId\\n    mediaType\\n    link\\n    __typename\\n  }\\n  ... on RadioEpisodeListenAction {\\n    streamId\\n    pageLink\\n    startDate\\n    __typename\\n  }\\n  ... on LiveListenAction {\\n    streamId\\n    livestreamPageLink\\n    startDate\\n    endDate\\n    __typename\\n  }\\n  ... on LiveWatchAction {\\n    streamId\\n    livestreamPageLink\\n    startDate\\n    endDate\\n    __typename\\n  }\\n}\\nfragment imageFragment on Image {\\n  __typename\\n  objectId\\n  alt\\n  title\\n  focalPoint\\n  templateUrl\\n}\\nfragment tileFragment on Tile {\\n  ... on IIdentifiable {\\n    __typename\\n    objectId\\n  }\\n  ... on IComponent {\\n    ...componentTrackingDataFragment\\n    __typename\\n  }\\n  ... on ITile {\\n    description\\n    title\\n    active\\n    action {\\n      ...actionFragment\\n      __typename\\n    }\\n    actionItems {\\n      ...actionItemFragment\\n      __typename\\n    }\\n    image {\\n      ...imageFragment\\n      __typename\\n    }\\n    primaryMeta {\\n      ...metaFragment\\n      __typename\\n    }\\n    secondaryMeta {\\n      ...metaFragment\\n      __typename\\n    }\\n    tertiaryMeta {\\n      ...metaFragment\\n      __typename\\n    }\\n    indexMeta {\\n      __typename\\n      type\\n      value\\n    }\\n    statusMeta {\\n      __typename\\n      type\\n      value\\n    }\\n    labelMeta {\\n      __typename\\n      type\\n      value\\n    }\\n    __typename\\n  }\\n  ... on ContentTile {\\n    brand\\n    brandLogos {\\n      ...brandLogosFragment\\n      __typename\\n    }\\n    __typename\\n  }\\n  ... on BannerTile {\\n    compactLayout\\n    backgroundColor\\n    textTheme\\n    brand\\n    brandLogos {\\n      ...brandLogosFragment\\n      __typename\\n    }\\n    ctaText\\n    passUserIdentity\\n    titleArt {\\n      objectId\\n      templateUrl\\n      __typename\\n    }\\n    __typename\\n  }\\n  ... on EpisodeTile {\\n    description\\n    formattedDuration\\n    available\\n    chapterStart\\n    action {\\n      ...actionFragment\\n      __typename\\n    }\\n    playAction: watchAction {\\n      pageUrl: videoUrl\\n      resumePointProgress\\n      resumePointTotal\\n      completed\\n      __typename\\n    }\\n    episode {\\n      __typename\\n      objectId\\n      program {\\n        __typename\\n        objectId\\n        link\\n      }\\n    }\\n    epgDuration\\n    __typename\\n  }\\n  ... on PodcastEpisodeTile {\\n    formattedDuration\\n    available\\n    programLink: podcastEpisode {\\n      objectId\\n      podcastProgram {\\n        objectId\\n        link\\n        __typename\\n      }\\n      __typename\\n    }\\n    playAction: listenAction {\\n      pageUrl: podcastEpisodeLink\\n      resumePointProgress\\n      resumePointTotal\\n      completed\\n      __typename\\n    }\\n    __typename\\n  }\\n  ... on PodcastProgramTile {\\n    link\\n    __typename\\n  }\\n  ... on ProgramTile {\\n    link\\n    __typename\\n  }\\n  ... on AudioLivestreamTile {\\n    brand\\n    brandsLogos {\\n      brand\\n      brandTitle\\n      logos {\\n        ...brandLogosFragment\\n        __typename\\n      }\\n      __typename\\n    }\\n    __typename\\n  }\\n  ... on LivestreamTile {\\n    description\\n    __typename\\n  }\\n  ... on ButtonTile {\\n    icon\\n    iconPosition\\n    mode\\n    __typename\\n  }\\n  ... on RadioEpisodeTile {\\n    action {\\n      ...actionFragment\\n      __typename\\n    }\\n    available\\n    epgDuration\\n    formattedDuration\\n    thumbnailMeta {\\n      ...metaFragment\\n      __typename\\n    }\\n    ...componentTrackingDataFragment\\n    __typename\\n  }\\n  ... on SongTile {\\n    startDate\\n    formattedStartDate\\n    endDate\\n    __typename\\n  }\\n  ... on RadioProgramTile {\\n    objectId\\n    __typename\\n  }\\n}\\nfragment metaFragment on MetaDataItem {\\n  __typename\\n  type\\n  value\\n  shortValue\\n  longValue\\n}\\nfragment componentTrackingDataFragment on IComponent {\\n  trackingData {\\n    data\\n    perTrigger {\\n      trigger\\n      data\\n      template {\\n        id\\n        __typename\\n      }\\n      __typename\\n    }\\n    __typename\\n  }\\n}\\nfragment brandLogosFragment on Logo {\\n  colorOnColor\\n  height\\n  mono\\n  primary\\n  type\\n  width\\n}\\nfragment paginatedTileListFragment on PaginatedTileList {\\n  __typename\\n  objectId\\n  listId\\n  actionItems {\\n    ...actionItemFragment\\n    __typename\\n  }\\n  banner {\\n    actionItems {\\n      ...actionItemFragment\\n      __typename\\n    }\\n    backgroundColor\\n    compactLayout\\n    description\\n    image {\\n      ...imageFragment\\n      __typename\\n    }\\n    textTheme\\n    title\\n    __typename\\n  }\\n  bannerSize\\n  displayType\\n  expires\\n  tileVariant\\n  paginatedItems(first: $lazyItemCount, after: $after, before: $before) {\\n    __typename\\n    edges {\\n      __typename\\n      cursor\\n      node {\\n        __typename\\n        ...tileFragment\\n      }\\n    }\\n    pageInfo {\\n      __typename\\n      endCursor\\n      hasNextPage\\n      hasPreviousPage\\n      startCursor\\n    }\\n  }\\n  sort {\\n    icon\\n    order\\n    title\\n    __typename\\n  }\\n  tileContentType\\n  tileOrientation\\n  title\\n  description\\n  ... on IComponent {\\n    ...componentTrackingDataFragment\\n    __typename\\n  }\\n}","operationName":"ProgramSeasonEpisodeList","variables":{"listId":"static:/vrtnu/a-z/-likeme/3.episodes-list.json"}}',
        method: 'POST',
      });

      // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
      const json: MoreSeasonsResponse = await res.json();
      for (const node of json.data.list.items) {
        if (node.__typename === 'EpisodeTile') {
          nodeList.push(node);
        }
      }
    } else if ([
      'PageHeader',
      'Banner',
      'Text',
      'TagsList',
    ].includes(comp.__typename)) {
      // ignore
      return [];
    } else {
      // look deeper for children
      if (comp.items) {
        for (const item of comp.items) {
          for (const childComp of item.components) {
            const nodes = await this.getAllEpisodeTileNodes(childComp);
            nodeList.push(...nodes);
          }
        }
      } else {
        console.log('No items found in', comp.__typename);
      }
    }
    console.log('Found', nodeList.length, 'EpisodeTile nodes');
    return nodeList;
  }
}
