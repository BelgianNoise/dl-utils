import asyncio
import os
import time
from loguru import logger

from ..models.dl_request import DLRequest
from ..models.dl_request_platform import DLRequestPlatform
from ..utils.browser import create_playwright_page, get_storage_state_location
from .VTMGO import process_dpg_media_download


async def handle_streamz_consent_popup(page):
  """
  Handle consent popup if it appears
  """
  try:
    logger.debug("Accepting cookies")
    await page.wait_for_selector("div.didomi-popup-container", timeout=2000)
  except:
    logger.debug("No consent popup found:")
    return
  acceptButton = await page.wait_for_selector("button#didomi-notice-agree-button")
  await acceptButton.click()
  logger.debug("Cookies accepted")

async def get_streamz_data(video_page_url: str):
  browser = None
  playwright = None
  config = None

  try:
    playwright, browser, page = await create_playwright_page(DLRequestPlatform.STREAMZ)

    await page.goto("https://www.streamz.be/", wait_until="networkidle")
    await handle_streamz_consent_popup(page)

    try:
      await page.wait_for_selector("li.nav__item--userdropdown", timeout=2000)
      logger.debug("Already logged in")
      await page.context.storage_state(
        path=get_storage_state_location(DLRequestPlatform.STREAMZ)
      )
    except:
      logger.debug("Logging in ...")
      await page.goto(
        "https://www.streamz.be/account/login?flow=authentication_only",
        wait_until="networkidle",
      )

      emailInput = await page.wait_for_selector("input#username")
      assert os.getenv("AUTH_STREAMZ_EMAIL"), "AUTH_STREAMZ_EMAIL not set"
      await emailInput.type(os.getenv("AUTH_STREAMZ_EMAIL"))

      passwordInput = await page.wait_for_selector("input#current-password")
      assert os.getenv("AUTH_STREAMZ_PASSWORD"), "AUTH_STREAMZ_PASSWORD not set"
      await passwordInput.type(os.getenv("AUTH_STREAMZ_PASSWORD"))

      submitButton = await page.wait_for_selector('button:has-text("Log in")')
      await submitButton.click()

      await page.wait_for_selector("li.nav__item--userdropdown", timeout=200000000)
      logger.debug("Logged in successfully")
      await page.context.storage_state(
        path=get_storage_state_location(DLRequestPlatform.STREAMZ)
      )

    config_response = None
    max_wait = 10
    while config_response is None:
      logger.debug(f"Config response attempt {10 - max_wait + 1}")
      if max_wait == 0:
        raise Exception("Failed to get config response, tried 10 times :/")
      max_wait -= 1
      def handle_response(response):
        nonlocal config_response
        if "https://videoplayer-service.dpgmedia.net/play-config/" in response.url:
          config_response = response
      page.on("response", handle_response)
      await page.goto(video_page_url, wait_until="load")
      await asyncio.sleep(4)

    logger.debug("Got config response")
    config = await config_response.json()

  finally:
    if browser is not None:
      await browser.close()
    if playwright is not None:
      await playwright.stop()

  return config


def STREAMZ_DL(dl_request: DLRequest):
  config = asyncio.run(get_streamz_data(dl_request.video_page_or_manifest_url))
  logger.debug(f"Config: {config}")

  return process_dpg_media_download(
    config,
    dl_request,
    DLRequestPlatform.STREAMZ,
    origin_url='https://www.streamz.be'
  )
