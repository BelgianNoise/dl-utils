import os
import time
import random
from loguru import logger

from ..models.dl_request import DLRequest
from ..models.dl_request_platform import DLRequestPlatform
from ..utils.browser import create_playwright_page, get_storage_state_location
from ..utils.browser_diagnostics import export_browser_diagnostics
from .VTMGO import process_dpg_media_download


def handle_streamz_consent_popup(page):
  """
  Handle consent popup if it appears
  """
  try:
    logger.debug("Accepting cookies")
    page.wait_for_selector("div.didomi-popup-container", timeout=2000)
  except:
    logger.debug("No consent popup found:")
    return
  acceptButton = page.wait_for_selector("button#didomi-notice-agree-button")
  acceptButton.click()
  logger.debug("Cookies accepted")

def get_streamz_data(video_page_url: str):
  browser = None
  config = None

  try:
    browser, page = create_playwright_page(DLRequestPlatform.STREAMZ)

    page.goto("https://www.streamz.be/", wait_until="networkidle")
    handle_streamz_consent_popup(page)

    try:
      page.wait_for_selector("li.nav__item--userdropdown", timeout=2000)
      logger.debug("Already logged in")
      page.context.storage_state(
        path=get_storage_state_location(DLRequestPlatform.STREAMZ)
      )
    except:
      logger.debug("Logging in ...")
      page.goto(
        "https://www.streamz.be/account/login?flow=authentication_only",
        wait_until="networkidle",
      )

      emailInput = page.wait_for_selector("input#username")
      assert os.getenv("AUTH_STREAMZ_EMAIL"), "AUTH_STREAMZ_EMAIL not set"
      emailInput.type(os.getenv("AUTH_STREAMZ_EMAIL"))

      passwordInput = page.wait_for_selector("input#current-password")
      assert os.getenv("AUTH_STREAMZ_PASSWORD"), "AUTH_STREAMZ_PASSWORD not set"
      passwordInput.type(os.getenv("AUTH_STREAMZ_PASSWORD"))

      submitButton = page.wait_for_selector('button:has-text("Log in")')
      submitButton.click()

      page.wait_for_selector("li.nav__item--userdropdown", timeout=200000000)
      logger.debug("Logged in successfully")
      page.context.storage_state(
        path=get_storage_state_location(DLRequestPlatform.STREAMZ)
      )

    # A single-element list is used so the inner handler can mutate it without
    # needing `nonlocal`. Python closures can mutate an outer object (list[0] = ...)
    # but cannot rebind a plain outer name (config = ...) without `nonlocal`.
    config = [None]

    def handle_response(response):
      if "https://videoplayer-service.dpgmedia.net/play-config/" in response.url:
        # Read the body immediately — Chrome's DevTools Protocol evicts response
        # bodies from its resource cache shortly after the request completes.
        # Calling .json() later (after a sleep) causes "No resource with given
        # identifier found".
        try:
          config[0] = response.json()
        except Exception as e:
          logger.warning(f"Failed to read play-config response body: {e}")
    page.on("response", handle_response)

    max_wait = 10
    while config[0] is None:
      logger.debug(f"Config response attempt {10 - max_wait + 1}")
      if max_wait == 0:
        export_browser_diagnostics(page, 'streamz-config-failed')
        raise Exception("Failed to get config response, tried 10 times :/")
      page.goto('about:blank', wait_until='load')
      max_wait -= 1
      page.goto(video_page_url, wait_until="load")
      time.sleep(3 + random.uniform(1, 3))

    logger.debug("Got config response")
    config = config[0]

    logger.debug("Got config response")

  finally:
    if browser is not None:
      browser.close()

  return config


def STREAMZ_DL(dl_request: DLRequest):
  config = get_streamz_data(dl_request.video_page_or_manifest_url)
  logger.debug(f"Config: {config}")

  return process_dpg_media_download(
    config,
    dl_request,
    DLRequestPlatform.STREAMZ,
    origin_url='https://www.streamz.be'
  )
