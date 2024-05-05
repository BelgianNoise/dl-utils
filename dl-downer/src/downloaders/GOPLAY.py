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
  try:
    playwright, browser, page = create_playwright_page(DLRequestPlatform.GOPLAY)

    page.goto("https://www.goplay.be/profiel", wait_until='networkidle')
    handle_goplay_consent_popup(page)

    try:
      page.wait_for_selector('span.profile-page__header__email', timeout=2000)
      logger.debug('Already logged in')
      page.context.storage_state(path=state_file)
    except:
      logger.debug('Logging in ...')
      openLogin = page.wait_for_selector('div.not-logged-in button')
      openLogin.click()
      emailInput = page.wait_for_selector('input#email')
      assert os.getenv('AUTH_GOPLAY_EMAIL'), 'AUTH_GOPLAY_EMAIL not set'
      emailInput.type(os.getenv('AUTH_GOPLAY_EMAIL'))
      passwordInput = page.wait_for_selector('input#password')
      assert os.getenv('AUTH_GOPLAY_PASSWORD'), 'AUTH_GOPLAY_PASSWORD not set'
      passwordInput.type(os.getenv('AUTH_GOPLAY_PASSWORD'))
      submitButton = page.wait_for_selector('form button[type="submit"]')
      submitButton.click()

      # find h2 element with test 'Mijn lijst'
      page.wait_for_selector('span.profile-page__header__email')
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
    for origin in state['origins']:
      if origin['origin'] == 'https://www.goplay.be':
        local_storage_entries = origin['localStorage']
        for entry in local_storage_entries:
          if entry['name'] and entry['name'].endswith('idToken'):
            bearer_token = entry['value']
            break
  logger.debug(f'Bearer: {bearer_token}')
  return bearer_token

def GOPLAY_DL(dl_request: DLRequest):

  # Parse video uuid from the page
  page_resp = requests.get(dl_request.video_page_or_manifest_url)
  page_content = page_resp.text
  obj_string = re.search(r'<div data-hero="(.+?)"', page_content).group(1)
  obj_string = re.sub(r'&quot;', '"', obj_string)
  obj = json.loads(obj_string)

  video_object = None
  if len(obj['data']['playlists']) == 0:
    # This is a movie
    video_object = obj['data']['movie']
  else:
    # This is a series
    for playlist in obj['data']['playlists']:
      for episode in playlist['episodes']:
        if episode['pageInfo']['url'] == dl_request.video_page_or_manifest_url.split('#')[0]:
          video_object = episode
          break

  video_uuid = video_object['videoUuid']
  type_form = video_object['type']
  type_form = re.sub('_', '-', type_form)
  is_drm = video_object['isDrm']
  if dl_request.output_filename is None:
    title = video_object['pageInfo']['title']
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
  content_source_id = video_data['ssai']['contentSourceID']
  logger.debug(f'Content source ID: {content_source_id}')
  video_id = video_data['ssai']['videoID']
  logger.debug(f'Video ID: {video_id}')

  # get video streams
  streams_resp = requests.post(f'https://dai.google.com/ondemand/dash/content/{content_source_id}/vid/{video_id}/streams')
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
    lic_res = requests.post('https://wv-keyos.licensekeyserver.com/', data=challenge, headers=headers)
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
  os.makedirs(os.path.dirname(final_file_move_to), exist_ok=True)
  os.rename(final_file, final_file_move_to)
  logger.debug(f'Downloaded {title} to {final_file_move_to}')
