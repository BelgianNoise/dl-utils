import json
import re
import os
import shutil
import requests

from loguru import logger


from ..mpd.mpd import MPD
from ..mpd.mpd_download_options import MPDDownloadOptions
from ..utils.browser import create_playwright_page, get_storage_state_location
from ..utils.download_video_nre import download_video_nre
from ..utils.local_cdm import Local_CDM
from ..utils.filename import parse_filename
from ..models.dl_request_platform import DLRequestPlatform
from ..models.dl_request import DLRequest

def handle_goplay_consent_popup(page):
  '''
  Handle consent popup if it appears
  '''
  try:
    logger.debug('Accepting cookies')
    page.wait_for_selector('#didomi-popup', timeout=2000)
  except:
    logger.debug(f'No consent popup found:')
    return
  acceptButton = page.wait_for_selector('button#didomi-notice-agree-button')
  acceptButton.click()
  logger.debug('Cookies accepted')

def extract_goplay_bearer_token() -> str:
  '''
  Get bearer token from a headless browser performing a real login
  '''
  bearer_token = ''
  state_file = get_storage_state_location(DLRequestPlatform.GOPLAY)

  browser = None
  playwright = None

  try:
    assert os.getenv('AUTH_GOPLAY_EMAIL'), 'AUTH_GOPLAY_EMAIL not set'
    assert os.getenv('AUTH_GOPLAY_PASSWORD'), 'AUTH_GOPLAY_PASSWORD not set'
    playwright, browser, page = create_playwright_page(DLRequestPlatform.GOPLAY)

    page.goto("https://www.goplay.be/profiel", wait_until='networkidle')
    handle_goplay_consent_popup(page)

    try:
      # Find the email on the page to check if we're already logged in
      assert os.getenv('AUTH_GOPLAY_EMAIL') in page.content(), 'Not logged in'
      logger.debug('Already logged in')
      page.context.storage_state(path=state_file)
    except:
      logger.debug('Logging in ...')
      # This used to be a popup, but now it's a link
      openLogin = page.wait_for_selector('a[href="/login"]')
      openLogin.click()
      emailInput = page.wait_for_selector('input#login-form-email')
      emailInput.type(os.getenv('AUTH_GOPLAY_EMAIL'))
      passwordInput = page.wait_for_selector('input#login-form-password')
      passwordInput.type(os.getenv('AUTH_GOPLAY_PASSWORD'))
      submitButton = page.wait_for_selector('form:has(input#login-form-email) button')
      submitButton.click()

      page.wait_for_selector('aside a[href="/"] svg')
      page.goto("https://www.goplay.be/profiel", wait_until='networkidle')
      assert os.getenv('AUTH_GOPLAY_EMAIL') in page.content(), 'Login failed'
      logger.debug('Logged in successfully')
      page.context.storage_state(path=state_file)

  finally:
    if browser is not None:
      browser.close()
    if playwright is not None:
      playwright.stop()

  # read idToken from state file
  with open(state_file, 'r') as f:
    state = json.load(f)
    # logger.debug(f'browser state: {json.dumps(state, indent=2)}')
    for cookie in state['cookies']:
      if cookie['domain'] == 'www.goplay.be':
        if cookie['name'].endswith('idToken'):
          bearer_token = cookie['value']
          break
  logger.debug(f'Bearer: {bearer_token}')
  return bearer_token

def GOPLAY_DL(dl_request: DLRequest):

  # Parse video uuid from the page
  page_resp = requests.get(dl_request.video_page_or_manifest_url)
  page_content = page_resp.text
  # Find the correct script tag that contains the video data
  scr_tag = re.search(r'<script>(?:(?!</?script>).)*playerContainer(?:(?!</?script>).)*</script>', page_content)
  if scr_tag is None:
    logger.error('No video data found')
    return
  full_obj_string = re.search(r'push\((.*)\)', scr_tag.group(0))
  obj_string_match = re.search(r'playerContainer.*?children.*?(\{.*?\})\]\}\]', full_obj_string.group(1))
  obj_string = obj_string_match.group(1).replace('\\"', '"')
  obj = json.loads(obj_string)

  video_object = obj['video']
  # logger.debug(f'Video object: {json.dumps(video_object, indent=2)}')
  video_uuid = video_object['uuid']
  type_form = video_object['videoType']
  # Transform 'longForm' to 'long-form' for the URL
  type_form = re.sub(r'([a-z])([A-Z])', r'\1-\2', type_form).lower()
  is_drm = video_object['flags']['isDrm']
  if dl_request.output_filename is None:
    title = video_object['title']
    title = parse_filename(title)
  else:
    title = dl_request.output_filename

  logger.debug(f'Video uuid: {video_uuid}')
  logger.debug(f'Type: {type_form}')
  logger.debug(f'Is DRM: {is_drm}')
  logger.debug(f'Title: {title}')

  # get video data
  video_data_url = f'https://api.goplay.be/web/v1/videos/{type_form}/{video_uuid}'
  logger.debug(f'Video data URL: {video_data_url}')
  bearer_token = extract_goplay_bearer_token()
  video_data_resp = requests.get(
    video_data_url,
    headers={ 'authorization': f'Bearer {bearer_token}' },
  )
  if video_data_resp.status_code != 200:
    logger.debug(video_data_resp.text)
  video_data = video_data_resp.json()
  # logger.debug(f'Video data: {json.dumps(video_data, indent=2)}')
  content_source_id = video_data['ssai']['contentSourceID']
  logger.debug(f'Content source ID: {content_source_id}')
  video_id = video_data['ssai']['videoID']
  logger.debug(f'Video ID: {video_id}')

  # get video streams
  streams_resp = requests.post(f'https://pubads.g.doubleclick.net/ondemand/dash/content/{content_source_id}/vid/{video_id}/streams')
  streams = streams_resp.json()
  stream_manifest = streams['stream_manifest']

  logger.debug(f'Stream manifest: {stream_manifest}')

  keys = {}

  if is_drm:
    drm_xml = video_data['drmXml']
    logger.debug(f'DRM XML: {drm_xml}')
    manifest_response = requests.get(stream_manifest)
    pssh = re.findall(r'<pssh[^>]*>(.{,120})</pssh>', manifest_response.text)[0]
    logger.debug(f'PSSH: {pssh}')
    cdm = Local_CDM()
    challenge = cdm.generate_challenge(pssh)
    headers = { 'Customdata': drm_xml }
    lic_res = requests.post('https://widevine.keyos.com/api/v4/getLicense', data=challenge, headers=headers)
    lic_res.raise_for_status()
    keys = cdm.decrypt_response(lic_res.content)
    logger.debug(f'Keys: {keys}')

  # use own downloader cause goplay's mpd file doesn't go well with n_m3u8dl_re
  mpd = MPD.from_url(stream_manifest)
  download_options = MPDDownloadOptions()
  # set the preferred quality matcher
  if dl_request.preferred_quality_matcher:
    download_options.video_resolution = dl_request.preferred_quality_matcher
  if len(keys) > 0:
    download_options.decrypt_keys = keys
  # ignore all periods prefixed with 'pre-roll'
  download_options.ignore_periods = [ '^pre-roll.*' ]
  # download the mpd
  final_file = mpd.download('./tmp', download_options)
  # move the final file to the downloads folder
  final_file_move_to = dl_request.get_full_filename_path(title)
  # We can't use shutil.move or os.rename because the destination
  # might be on a different filesystem depending on the configuration
  shutil.copy(final_file, final_file_move_to)
  os.remove(final_file)
  logger.debug(f'Downloaded {title} to {final_file_move_to}')
