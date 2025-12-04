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
  config = None

  try:
    browser, page = create_playwright_page(DLRequestPlatform.VTMGO)

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

      # There might be a profile selection screen, if not, skip it
      try:
        page.wait_for_selector('div.profile button.profile__link', timeout=5000)
      except:
        logger.debug('No profile selection screen detected, continuing ...')
      else:
        profileButton = page.wait_for_selector('div.profile button.profile__link')
        profileButton.click()

      page.wait_for_selector('li.nav__item--userdropdown', timeout=200000000)
      logger.debug('Logged in successfully')
      page.context.storage_state(path=get_storage_state_location(DLRequestPlatform.VTMGO))

    config_response = None
    max_wait = 10
    while config_response is None:
      logger.debug(f'Config response attempt {10 - max_wait + 1}')
      if max_wait == 0:
        raise Exception('Failed to get config response, tried 10 times :/')
      max_wait -= 1
      def handle_response(response):
        nonlocal config_response
        if 'https://videoplayer-service.dpgmedia.net/play-config/' in response.url:
          config_response = response
      page.on('response', handle_response)
      page.goto(video_page_url, wait_until='load')
      time.sleep(4)

    logger.debug('Got config response')
    config = config_response.json()

  finally:
    if browser is not None:
      browser.close()

  return config

def extract_dash_stream_info(config) -> dict:
  """Extract DASH stream information from config"""
  streams = config['video']['streams']
  dash_stream = None
  for stream in streams:
    if stream['type'] == 'dash':
      dash_stream = stream
      break
  assert dash_stream, 'No dash stream found'

  return {
    'mpd_url': dash_stream['url'],
    'license_url': dash_stream['drm']['com.widevine.alpha']['licenseUrl'],
    'auth_token': dash_stream['drm']['com.widevine.alpha']['drmtoday']['authToken'],
  }

def generate_filename_from_metadata(config, output_filename=None):
  """Generate filename from metadata or use provided filename"""
  if output_filename:
    return output_filename

  metadata = config['video']['metadata']
  if 'episode' not in metadata:
    # Movie
    title = metadata['title']
    filename = f'{title}'
  else:
    # Series
    ep_order = metadata['episode'].get('order')
    ep = ep_order if ep_order is not None else 0
    season = metadata['episode']['season']['order']
    title = metadata['program']['title']
    filename = f'{title}.S{season:02}E{ep:02}'

  return parse_filename(filename)

def get_pssh_from_manifest(mpd_url):
  """Extract PSSH from MPD manifest"""
  manifest_response = requests.get(mpd_url)
  manifest_response.raise_for_status()
  logger.debug(f'Manifest response status: {manifest_response.status_code}')

  try:
    pssh = re.findall(r'<cenc:pssh[^>]*>(.{,240})</cenc:pssh>', manifest_response.text)[0]
    assert pssh
    return pssh
  except:
    raise Exception(f'Failed to find pssh in manifest: {manifest_response.text}')

def get_widevine_keys(pssh, license_url, auth_token, origin_url='https://www.vtmgo.be'):
  """Get Widevine decryption keys"""
  cdm = Local_CDM()
  challenge = cdm.generate_challenge(pssh)
  headers = {
    'user-agent': user_agent,
    'origin': origin_url,
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
  return keys

def download_and_insert_subtitles(config, downloaded_file, preferred_lang='nl-tt'):
  """Download and insert subtitles if available"""
  if 'subtitles' not in config['video']:
    return

  subtitles = config['video']['subtitles']
  subtitle = None

  # Try to find preferred language subtitle
  for sub in subtitles:
    if sub['language'] == preferred_lang:
      subtitle = sub
      break

  # Fall back to first subtitle if preferred not found
  if subtitle is None and subtitles:
    subtitle = subtitles[0]

  if subtitle is None:
    return

  subtitle_url = subtitle['url']
  logger.debug(f'Subtitle: {subtitle_url}')

  # Download the subtitle and store it next to the video
  subtitle_response = requests.get(subtitle_url)
  subtitle_response.raise_for_status()
  subtitle_filename = f'{downloaded_file}.vtt'
  with open(subtitle_filename, 'wb') as f:
    f.write(subtitle_response.content)
  logger.debug(f'Subtitle saved to {subtitle_filename}')
  insert_subtitle(downloaded_file, subtitle_filename)
  os.remove(subtitle_filename)

def process_dpg_media_download(config, dl_request, platform, origin_url='https://www.vtmgo.be'):
  """
  Common download logic for DPG Media platforms (VTMGO, STREAMZ)
  This can be called from both VTMGO_DL and STREAMZ_DL functions
  """
  # Extract stream info
  stream_info = extract_dash_stream_info(config)
  mpd_url = stream_info['mpd_url']
  license_url = stream_info['license_url']
  auth_token = stream_info['auth_token']

  logger.debug(f'MPD: {mpd_url}')
  logger.debug(f'License: {license_url}')
  logger.debug(f'Auth token: {auth_token}')

  # Generate filename
  filename = generate_filename_from_metadata(config, dl_request.output_filename)
  logger.debug(f'Filename: {filename}')

  # Get PSSH and keys
  pssh = get_pssh_from_manifest(mpd_url)
  logger.debug(f'PSSH: {pssh}')

  # Get Widevine keys with platform-specific origin
  keys = get_widevine_keys(pssh, license_url, auth_token, origin_url)

  # Download video
  downloaded_file = download_video_nre(
    mpd_url,
    filename,
    platform,
    dl_request.preferred_quality_matcher,
    keys=keys,
  )

  # Handle subtitles
  download_and_insert_subtitles(config, downloaded_file)

  return downloaded_file

def VTMGO_DL(dl_request: DLRequest):
  config = get_vtmgo_data(dl_request.video_page_or_manifest_url)
  return process_dpg_media_download(config, dl_request, DLRequestPlatform.VTMGO)
