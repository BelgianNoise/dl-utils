import os
from loguru import logger

from playwright.sync_api import sync_playwright
from playwright.sync_api import Browser, Page

from ..models.dl_request_platform import DLRequestPlatform

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
  )
  page = custom_context.new_page()

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

    // window.chrome is present in real Chrome but missing in headless builds.
    // Shaka-player and other scripts check for its existence.
    if (!window.chrome) window.chrome = { runtime: {} };

    // Prevent detection via the Permissions API (headless returns a different state).
    const _query = window.Permissions && window.Permissions.prototype.query;
    if (_query) {
      window.Permissions.prototype.query = (parameters) =>
        parameters.name === 'notifications'
          ? Promise.resolve({ state: Notification.permission })
          : _query(parameters);
    }
  """)

  return (browser, page)
