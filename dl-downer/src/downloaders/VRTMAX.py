import base64
import hashlib
import hmac
import json
import re
import os
import shutil
import requests
import time
from loguru import logger
from urllib.parse import urlparse

from ..pssh_box import pssh_box
from ..mpd.mpd import MPD
from ..mpd.mpd_download_options import MPDDownloadOptions
from ..models.dl_request_platform import DLRequestPlatform
from ..models.dl_request import DLRequest
from ..utils.filename import parse_filename
from ..utils.local_cdm import Local_CDM
from ..utils.download_video_nre import download_video_nre
from ..utils.browser import create_playwright_page, get_storage_state_location, user_agent
from .const.VRTMAX_graphql_query import VRTMAX_graphql_query

headers = {
  'User-Agent': user_agent,
  'Content-Type': 'application/json',
  'x-vrt-client-name': 'WEB',
}

def handle_vrt_consent_popup(page):
  '''
  Handle consent popup if it appears
  '''

  try:
    logger.debug('Accepting cookies')
    page.wait_for_selector('iframe[src*="consent"]', timeout=2000)
  except:
    logger.debug(f'No consent popup found:')
    return
  frame = page.frame_locator('iframe[src*="consent"]')
  acceptButton = frame.get_by_text('Alles accepteren')
  acceptButton.click()
  logger.debug('Cookies accepted')

def extract_vrt_cookies():
  '''
  Get cookies from a headless browser performing a real login

  :returns: cookies List[Cookies], vrt_token: str
  '''

  browser = None

  try:
    browser, page = create_playwright_page(DLRequestPlatform.VRTMAX)

    page.goto("https://www.vrt.be/vrtmax/", wait_until='networkidle')
    handle_vrt_consent_popup(page)

    wait_for_logged_in_selector = 'header button[aria-label^="Profielmenu:"]:not([aria-label="Profielmenu: Aanmelden"])'
    wait_for_logged_out_selector = 'header button[aria-label="Profielmenu: Aanmelden"]'

    try:
      page.wait_for_selector(wait_for_logged_in_selector, timeout=5000)
      logger.debug('Already logged in')
      cookies = page.context.cookies()
      page.context.storage_state(path=get_storage_state_location(DLRequestPlatform.VRTMAX))
    except:
      logger.debug('Logging in ...')
      loginButton = page.wait_for_selector(wait_for_logged_out_selector, timeout=10000)
      loginButton.click()
      emailInput = page.wait_for_selector('input#email-id-email')
      assert os.getenv('AUTH_VRTMAX_EMAIL'), 'AUTH_VRTMAX_EMAIL not set'
      emailInput.type(os.getenv('AUTH_VRTMAX_EMAIL'))
      passwordInput = page.wait_for_selector('input#password-id-password')
      assert os.getenv('AUTH_VRTMAX_PASSWORD'), 'AUTH_VRTMAX_PASSWORD not set'
      passwordInput.type(os.getenv('AUTH_VRTMAX_PASSWORD'))
      submitButton = page.wait_for_selector('form button[type="submit"]')
      submitButton.click()

      page.wait_for_selector(wait_for_logged_in_selector, timeout=10000)
      logger.debug('Logged in successfully')
      cookies = page.context.cookies()
      page.context.storage_state(path=get_storage_state_location(DLRequestPlatform.VRTMAX))

  finally:
    if browser is not None:
      browser.close()

  # get cookie named 'vrtnu-site_profile_vt'
  vrt_token = next(c['value'] for c in cookies if c['name'] == 'vrtnu-site_profile_vt')
  logger.debug(f'VRT token: {vrt_token}')
  return (cookies, vrt_token)

def get_graphql_metadata(url_path, cookies):
  '''
  Get video metadata from GraphQL API

  :return: tuple of program title, name, and stream_id
  '''
  json_data = {
    'query': VRTMAX_graphql_query,
    'operationName': 'EpisodePage',
    'variables': {
      'pageId': url_path,
    },
  }

  response = requests.post('https://www.vrt.be/vrtnu-api/graphql/public/v1', cookies=cookies, headers=headers, json=json_data)
  logger.debug(f'GraphQL response: {response.text}')
  body = response.json()
  bodyString = json.dumps(body)

  program_title = body['data']['page']['player']['subtitle']
  # "<program_title> - s<year>a<episode> - <dd/mm/yyyy hh:mm>"
  # source_program_name = body['data']['page']['modes'][0]['cimMediaTrackingData']['programName'].

  episode = None
  season = None
  # parse season and episode from metadata (loop over secondary metadata)
  season = None
  episode = None

  # find first occurence of /[sS](\d+)[aA](\d+)/
  regex_result = re.search(r'[sS](\d+)[aAeE](\d+)', bodyString)
  if regex_result:
    season = regex_result.group(1).zfill(2)
    episode = regex_result.group(2).zfill(2)
  if not season:
    # find occurence of /Seizoen\s(\d+)/
    regex_result = re.search(r'Seizoen\s(\d+)', bodyString)
    if regex_result:
      season = regex_result.group(1).zfill(2)
  if not season:
    # find occurence of /\"$sena\":\"([^\"]+)\"/
    regex_result = re.search(r'\"\$sena\":\"([^\"]+)\"', bodyString)
    if regex_result:
      season = regex_result.group(1).zfill(2)

  if not episode:
    # find occurence of /Aflevering\s(\d+)/
    regex_result = re.search(r'Aflevering\s(\d+)', bodyString)
    if regex_result:
      episode = regex_result.group(1).zfill(2)
  if not episode:
    # find occurence of /\"$epnu\":(\d+)/
    regex_result = re.search(r'\"\$epnu\":(\d+)', bodyString)
    if regex_result:
      episode = regex_result.group(1).zfill(2)
  if not episode:
    # find occurence of /\"episodeNumber\":(\d+)/
    regex_result = re.search(r'\"episodeNumber\":(\d+)', bodyString)
    if regex_result:
      episode = regex_result.group(1).zfill(2)

  if season and episode:
    title = f'{program_title} S{season}E{episode}' # should always occur for series
  else:
    title = program_title # usually occurs for movies
  logger.debug(f'Title: {title}')

  stream_id = body['data']['page']['player']['modes'][0]['streamId']
  logger.debug(f'Stream ID: {stream_id}')
  if not stream_id:
    raise Exception('Stream ID not found in GraphQL response')

  return (title, stream_id)

def get_video_token(vrt_token, player_info):
  '''
  Get video token from VRT API

  :return: video_token
  '''
  json_data = {
    'identityToken': vrt_token,
    'playerInfo': player_info
  }

  response = requests.post(
    'https://media-services-public.vrt.be/vualto-video-aggregator-web/rest/external/v2/tokens',
    headers=headers,
    json=json_data,
  )
  body = response.json()

  video_token = body['vrtPlayerToken']
  logger.debug(f'Video token: {video_token}')

  return video_token

def get_video_metadata(stream_id, video_token):
  '''
  Get video file metadata from VRT API

  :return: tuple of drm_token and mpd_url
  '''
  params = {
    'vrtPlayerToken': video_token,
    'client': 'vrtnu-web@PROD',
  }

  response = requests.get(
    'https://media-services-public.vrt.be/media-aggregator/v2/media-items/' + stream_id,
    params=params,
    headers=headers,
  )
  body = response.json()

  drm_token = body['drm']
  logger.debug(f'DRM token: {drm_token}')

  mpd_url = list(filter(lambda t: t['type'] == 'mpeg_dash', body['targetUrls']))[0]['url']
  logger.debug(f'MPD URL: {mpd_url}')

  return (drm_token, mpd_url)

def get_license_response(challengeBinary, drm_token):
  '''
  Get Widevine response from Vualto license server

  :return: Widevine reponse in base64
  '''
  challenge_b64 = base64.b64encode(challengeBinary).decode('utf-8')
  data = {
    'drm_info': challenge_b64,
    'token':  drm_token,
  }
  resp = requests.post(
    'https://widevine-proxy.drm.technology/proxy',
    json=data,
    headers={
      'Origin': 'https://www.vrt.be',
      'Referer': 'https://www.vrt.be/',
      'User-Agent': user_agent,
      'X-Vudrm-Token': drm_token,
      'Content-Type': 'application/json',
    }
  )
  resp.raise_for_status()
  response_bytes = resp.content
  response_b64 = base64.b64encode(response_bytes).decode('utf-8')
  logger.debug(f'Response: {response_b64}')

  return response_b64

def get_pssh_box(mpd_url: str) -> str:
  if 'remix.ism' in mpd_url:
    content_id = urlparse(mpd_url).path.split('/')[2]
  else:
    pattern = r'((?:vid|pl)-[^/]+?)(?=_drm|\.ism|/)'
    match = re.search(pattern, mpd_url)
    assert match, f'Failed to extract content ID from MPD URL: {mpd_url}'
    content_id = match.group(1)

  logger.debug(f'Content ID: {content_id}')
  pssh = pssh_box.main([
    '--widevine-system-id',
    '--content-id', bytes(content_id, "utf-8").hex(),
    '--protection-scheme', 'cenc',
    '--base64',
  ], force_protection_scheme=True)
  return pssh

def VRTMAX_DL(dl_request: DLRequest):

  url = dl_request.video_page_or_manifest_url
  url_path = urlparse(url).path.rstrip('/')

  # Get VRT cookies
  cookies, vrt_token = extract_vrt_cookies()
  # Transform List[Cookies] into RequestsCookieJar
  cookies = requests.utils.cookiejar_from_dict({c['name']:c['value'] for c in cookies})

  title, stream_id = get_graphql_metadata(url_path, cookies)
  video_token = get_video_token(vrt_token, '')
  drm_token, mpd_url = get_video_metadata(stream_id, video_token)

  filename = dl_request.output_filename
  if not filename:
    filename = parse_filename(title)
  logger.debug(f'Filename: {filename}')

  # retrieve the keys if DRM
  keys = {}
  if '_drm_' in mpd_url or drm_token:
    pssh = get_pssh_box(mpd_url)
    logger.debug(f'PSSH: {pssh}')

    myCDM = Local_CDM()
    challenge = myCDM.generate_challenge(pssh)
    response = get_license_response(challenge, drm_token)
    keys = myCDM.decrypt_response(response)
    myCDM.close()

  # download the video
  download_video_nre(
    mpd_url,
    filename,
    DLRequestPlatform.VRTMAX,
    dl_request.preferred_quality_matcher,
    keys=keys,
  )
  return
  # ---------- Using own MPD downloader ----------
  # initalize mpd object
  mpd = MPD.from_url(mpd_url)
  download_options = MPDDownloadOptions()
  if dl_request.preferred_quality_matcher:
    download_options.video_resolution = dl_request.preferred_quality_matcher
  if len(keys) > 0:
    download_options.keys = keys
  logger.debug('No DRM detected, downloading without decryption')
  final_file = mpd.download('./tmp', download_options)
  # move the final file to the downloads folder
  final_file_move_to = dl_request.get_full_filename_path(filename)
  shutil.move(final_file, final_file_move_to)
  logger.debug(f'Downloaded {filename} to {final_file_move_to}')
