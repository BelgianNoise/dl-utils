import os
from loguru import logger

from playwright.async_api import async_playwright
from playwright.async_api import Browser, Page, Playwright
from playwright_stealth import stealth_async

from ..models.dl_request_platform import DLRequestPlatform

user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 OPR/114.0.0.0'

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

async def create_playwright_page(platform: DLRequestPlatform) -> tuple[Playwright, Browser, Page]:
  '''
  Create a playwright browser and page with the correct state for the given platform.
  
  :return: a tuple containing the playwright instance, browser, and page objects
  '''

  playwright = await async_playwright().start()
  browser = await playwright.chromium.launch(
    headless=os.getenv('HEADLESS', 'true') == 'true',
    slow_mo=200,
  )
  custom_context = await browser.new_context(
    user_agent=user_agent,
    locale='nl-BE',
    storage_state=get_storage_state_location(platform),
  )
  page = await custom_context.new_page()
  await stealth_async(page)

  return (playwright, browser, page)
