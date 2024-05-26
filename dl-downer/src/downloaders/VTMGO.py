import os
import re
import time
import requests

from loguru import logger

from ..models.dl_request import DLRequest
from ..models.dl_request_platform import DLRequestPlatform
from ..utils.download_video_nre import download_video_nre
from ..utils.local_cdm import Local_CDM
from ..utils.filename import parse_filename
from ..utils.files import insert_subtitle
from ..utils.browser import create_playwright_page, get_storage_state_location, user_agent

def handle_vtmgo_consent_popup(page):
  '''
  Handle consent popup if it appears
  '''

  try:
    logger.debug('Accepting cookies')
    page.wait_for_selector('div#pg-first-layer', timeout=2000)
  except:
    logger.debug(f'No consent popup found:')
    return
  acceptButton = page.wait_for_selector('button#pg-accept-btn')
  acceptButton.click()
  logger.debug('Cookies accepted')

def get_vtmgo_data(video_page_url: str):
  browser = None
  playwright = None

  config = None

  try:
    playwright, browser, page = create_playwright_page(DLRequestPlatform.VTMGO)

    page.goto("https://www.vtmgo.be/vtmgo", wait_until='networkidle')
    handle_vtmgo_consent_popup(page)

    try:
      page.wait_for_selector('li.nav__item--userdropdown', timeout=2000)
      logger.debug('Already logged in')
      page.context.storage_state(path=get_storage_state_location(DLRequestPlatform.VTMGO))
    except:
      logger.debug('Logging in ...')
      page.goto('https://www.vtmgo.be/vtmgo/aanmelden', wait_until='networkidle')

      emailInput = page.wait_for_selector('input#username')
      assert os.getenv('AUTH_VTMGO_EMAIL'), 'AUTH_VTMGO_EMAIL not set'
      emailInput.type(os.getenv('AUTH_VTMGO_EMAIL'))
      submitButton = page.wait_for_selector('form button[type="submit"]')
      submitButton.click()

      passwordInput = page.wait_for_selector('input#password')
      assert os.getenv('AUTH_VTMGO_PASSWORD'), 'AUTH_VTMGO_PASSWORD not set'
      passwordInput.type(os.getenv('AUTH_VTMGO_PASSWORD'))
      submitButton = page.wait_for_selector('form button[type="submit"]')
      submitButton.click()

      page.wait_for_selector('li.nav__item--userdropdown', timeout=200000000)
      logger.debug('Logged in successfully')
      page.context.storage_state(path=get_storage_state_location(DLRequestPlatform.VTMGO))

    config_response = None
    def handle_response(response):
      nonlocal config_response
      if 'https://videoplayer-service.dpgmedia.net/play-config/' in response.url:
        config_response = response
    page.on('response', handle_response)
    page.goto(video_page_url, wait_until='load')
    max_wait = 10
    while config_response is None:
      time.sleep(2)
      if max_wait == 0:
        raise Exception('Failed to get config response')
      max_wait -= 1
    logger.debug('Got config response')
    config = config_response.json()

  finally:
    if browser is not None:
      browser.close()
    if playwright is not None:
      playwright.stop()

  return config

def VTMGO_DL(dl_request: DLRequest):
  config = get_vtmgo_data(dl_request.video_page_or_manifest_url)

  # find dash stream
  streams = config['video']['streams']
  dash_stream = None
  for stream in streams:
    if stream['type'] == 'dash':
      dash_stream = stream
      break
  assert dash_stream, 'No dash stream found'

  mpd_url = dash_stream['url']
  license_url = dash_stream['drm']['com.widevine.alpha']['licenseUrl']
  auth_token = dash_stream['drm']['com.widevine.alpha']['drmtoday']['authToken']
  logger.debug(f'MPD: {mpd_url}')
  logger.debug(f'License: {license_url}')
  logger.debug(f'Auth token: {auth_token}')

  filename = None
  if dl_request.output_filename:
    filename = dl_request.output_filename
  else:
    # use metadata to generate filename
    metadata = config['video']['metadata']
    prog = metadata['program']['title']
    ep = metadata['episode']['order']
    season = metadata['episode']['season']['order']
    filename = f'{prog}.S{season:02}E{ep:02}'
    filename = parse_filename(filename)
  logger.debug(f'Filename: {filename}')
  
  # get pssh from mpd
  manifest_response = requests.get(mpd_url)
  manifest_response.raise_for_status()
  pssh = re.findall(r'<cenc:pssh[^>]*>(.{,180})</cenc:pssh>', manifest_response.text)[0]
  logger.debug(f'PSSH: {pssh}')

  cdm = Local_CDM()
  challenge = cdm.generate_challenge(pssh)
  headers = {
    'user-agent': user_agent,
    'origin': 'https://www.vtmgo.be',
    'connection': 'keep-alive',
    'accept': '*/*',
    'accept-encoding': 'gzip, deflate, br',
    'X-Dt-Auth-Token': auth_token,
  }
  license_response = requests.post(license_url, data=challenge, headers=headers)
  license_response.raise_for_status()
  license_response_json = license_response.json()
  license = license_response_json['license']
  logger.debug(f'License: {license}')
  keys = cdm.parse_license(license)
  cdm.close()

  downloaded_file = download_video_nre(
    mpd_url,
    filename,
    DLRequestPlatform.VTMGO,
    dl_request.preferred_quality_matcher,
    keys=keys,
  )

  # find 'nl-tt' subtitle or default to first subtitle
  subtitles = config['video']['subtitles']
  subtitle = None
  for sub in subtitles:
    if sub['language'] == 'nl-tt':
      subtitle = sub
      break
  if subtitle is None:
    subtitle = subtitles[0]
  subtitle_url = subtitle['url']
  logger.debug(f'Subtitle: {subtitle_url}')

  # download the subtitle and store it next to the video
  subtitle_response = requests.get(subtitle_url)
  subtitle_response.raise_for_status()
  subtitle_filename = f'{downloaded_file}.vtt'
  with open(subtitle_filename, 'wb') as f:
    f.write(subtitle_response.content)
  logger.debug(f'Subtitle saved to {subtitle_filename}')
  insert_subtitle(downloaded_file, subtitle_filename)
  os.remove(subtitle_filename)

  return
