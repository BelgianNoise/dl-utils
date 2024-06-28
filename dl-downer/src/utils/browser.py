import os
from loguru import logger

from playwright.sync_api import sync_playwright
from playwright.sync_api import Browser, Page, Playwright
from playwright_stealth import stealth_sync

from ..models.dl_request_platform import DLRequestPlatform

user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 OPR/107.0.0.0'

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

def create_playwright_page(platform: DLRequestPlatform) -> tuple[Playwright, Browser, Page]:
  '''
  Create a playwright browser and page with the correct state for the given platform.
  
  :return: a tuple containing the browser and page objects
  '''

  playwright = sync_playwright().start()
  engine = playwright.webkit if platform == DLRequestPlatform.VTMGO else playwright.chromium
  browser = engine.launch(
    headless=os.getenv('HEADLESS', 'true') == 'true',
    slow_mo=200,
  )
  custom_context = browser.new_context(
    user_agent=user_agent,
    locale='nl-BE',
    storage_state=get_storage_state_location(platform),
  )
  page = custom_context.new_page()
  stealth_sync(page)

  return (playwright, browser, page)
