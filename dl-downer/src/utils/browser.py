import os
from loguru import logger

from playwright.sync_api import sync_playwright
from playwright.sync_api import Browser, Page

from ..models.dl_request_platform import DLRequestPlatform
from .browser_diagnostics import attach_diagnostics_listeners

user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'
playwright = sync_playwright().start()

def get_storage_state_location(platform: DLRequestPlatform) -> str:
  '''
  Get the location of the storage state file for the given platform.
  
  :param platform: the platform for which the storage state file is needed
  :return: the location of the storage state file
  '''
  p = os.getenv('STORAGE_STATES_FOLDER', './storage_states')
  # add "/" at the end if not already there
  if not p.endswith('/'):
    p += '/'
  p += f'{platform.value}.json'

  # if file does not exist, create it
  if not os.path.isfile(p):
    logger.debug(f'Creating storage state file for {platform.value}')
    with open(p, 'w') as f:
      f.write('{}')

  return p

def create_playwright_page(platform: DLRequestPlatform) -> tuple[Browser, Page]:
  '''
  Create a playwright browser and page with the correct state for the given platform.
  
  :return: a tuple containing the browser and page objects
  '''

  # playerwright.stop() cleans up the full /tmp folder
  # if it doesnt exist, create it
  if not os.path.exists('/tmp'):
    logger.debug('/tmp does not exist, creating it')
    os.makedirs('/tmp', exist_ok=True)

  browser = playwright.chromium.launch(
    headless=os.getenv('HEADLESS', 'true') == 'true',
    slow_mo=200,
    args=[
      # Suppresses the "Chrome is being controlled by automated software" banner
      # and removes the most commonly checked automation flag from the browser internals.
      '--disable-blink-features=AutomationControlled',
      # Required when running as root inside Docker containers.
      '--no-sandbox',
      # Hides the "Chrome is being controlled..." info bar in non-headless mode.
      '--disable-infobars',
      # Avoids crashes in Docker where /dev/shm is limited.
      '--disable-dev-shm-usage',
      # Extensions can interfere with page behaviour; disable them for consistency.
      '--disable-extensions',
    ],
  )
  custom_context = browser.new_context(
    user_agent=user_agent,
    locale='nl-BE',
    storage_state=get_storage_state_location(platform),
    # Use a realistic full-HD resolution. The headless default (1280x720) is a
    # well-known bot fingerprint that detection scripts actively check for.
    viewport={'width': 1920, 'height': 1080},
    screen={'width': 1920, 'height': 1080},
    java_script_enabled=True,
    # Match the timezone to the nl-BE locale to avoid locale/timezone mismatches,
    # which are another signal used by bot-detection scripts.
    timezone_id='Europe/Brussels',
    # Playwright's default Accept/Accept-Encoding headers differ slightly from
    # real Chrome's and can be used to fingerprint automated browsers.
    # These values match what Chrome 136 sends on a real Windows machine.
    extra_http_headers={
      'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
      'Accept-Encoding': 'gzip, deflate, br, zstd',
      'Accept-Language': 'nl-BE,nl;q=0.9,en-US;q=0.8,en;q=0.7',
    },
  )
  page = custom_context.new_page()
  attach_diagnostics_listeners(page)

  # Self-contained stealth script injected before every page load.
  # We intentionally avoid playwright_stealth (last release 1.0.6, unmaintained):
  # its navigator.vendor getter references an `opts` closure variable that leaks
  # out of scope, causing a ReferenceError when video players (e.g. shaka-player)
  # read navigator.vendor — crashing the page before any network requests fire.
  page.add_init_script("""
    // Hide the automation flag — the most commonly checked bot signal.
    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});

    // Real browsers have a non-empty plugins list; headless Chrome has none.
    Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});

    // Align languages with the nl-BE locale set on the browser context.
    Object.defineProperty(navigator, 'languages', {get: () => ['nl-BE', 'nl', 'en-US', 'en']});

    // navigator.vendor is 'Google Inc.' in real Chrome; empty string in some headless builds.
    Object.defineProperty(navigator, 'vendor', {get: () => 'Google Inc.'});

    // Running inside a Linux Docker container (e.g. on a QNAP NAS) while the
    // User-Agent claims Windows causes a detectable OS mismatch.
    // navigator.platform and navigator.userAgentData.platform must be patched to
    // match the Windows UA, otherwise bot detectors flag the contradiction.
    Object.defineProperty(navigator, 'platform', {get: () => 'Win32'});

    // navigator.userAgentData is the modern Client Hints API. It exposes the OS
    // platform independently of the UA string. On Linux this returns 'Linux',
    // contradicting our Windows UA. We override the whole object to be consistent.
    Object.defineProperty(navigator, 'userAgentData', {
      get: () => ({
        brands: [
          {brand: 'Chromium', version: '136'},
          {brand: 'Google Chrome', version: '136'},
          {brand: 'Not.A/Brand', version: '99'},
        ],
        mobile: false,
        platform: 'Windows',
        getHighEntropyValues: (hints) => Promise.resolve({
          architecture: 'x86',
          bitness: '64',
          mobile: false,
          model: '',
          platform: 'Windows',
          platformVersion: '10.0.0',
          uaFullVersion: '136.0.0.0',
          fullVersionList: [
            {brand: 'Chromium', version: '136.0.0.0'},
            {brand: 'Google Chrome', version: '136.0.0.0'},
            {brand: 'Not.A/Brand', version: '99.0.0.0'},
          ],
        }),
      }),
    });

    // window.chrome is present in real Chrome but missing in headless builds.
    // Shaka-player and other scripts check for its existence.
    // Detection scripts sometimes probe deeper than just existence — they call
    // runtime.connect() or runtime.sendMessage() and check the return type.
    // Stub out the most commonly probed methods to avoid throwing on access.
    if (!window.chrome) {
      window.chrome = {
        runtime: {
          connect: () => ({
            onMessage: { addListener: () => {} },
            onDisconnect: { addListener: () => {} },
            postMessage: () => {},
            disconnect: () => {},
          }),
          sendMessage: () => {},
          onMessage: { addListener: () => {} },
          id: undefined,
        },
        loadTimes: () => ({}),
        csi: () => ({}),
      };
    }

    // Prevent detection via the Permissions API (headless returns a different state).
    const _query = window.Permissions && window.Permissions.prototype.query;
    if (_query) {
      window.Permissions.prototype.query = function(parameters) {
        return parameters.name === 'notifications'
          ? Promise.resolve({ state: Notification.permission })
          : _query.call(this, parameters);
      };
    }
  """)

  return (browser, page)
