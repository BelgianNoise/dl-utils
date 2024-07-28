import base64
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
  # logger.debug(f'Video object: {video_object}')
  video_uuid = video_object['uuid']
  type_form = video_object['videoType']
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

  stream_collection = video_object['streamCollection']
  stream_collection_streams = stream_collection['streams']
  stream_drm_protected = stream_collection['drmProtected']
  # Find dash stream
  stream_manifest = ''
  for stream in stream_collection_streams:
    if stream['protocol'] == 'dash':
      stream_manifest = stream['url']
      break
  if stream_manifest == '':
    logger.error('No dash stream found')
    return
  logger.debug(f'Stream manifest: {stream_manifest}')
  logger.debug(f'DRM protected: {stream_drm_protected}')

  keys = {}

  if is_drm or stream_drm_protected:
    raise NotImplementedError('DRM protected content not supported')
    manifest_response = requests.get(stream_manifest)
    pssh = re.findall(r'<cenc:pssh[^>]*>(.{,120})</cenc:pssh>', manifest_response.text)[0]
    logger.debug(f'PSSH: {pssh}')
    cdm = Local_CDM()
    challenge = cdm.generate_challenge(pssh)
    drm_key = stream_collection['drmKey']
    custom_data_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<KeyOSAuthenticationXML>
  <Data>
    <WidevinePolicy fl_CanPersist="false" fl_CanPlay="true"/>
    <WidevineContentKeySpec TrackType="HD">
      <SecurityLevel>1</SecurityLevel>
      <RequiredHDCP>HDCP_NONE</RequiredHDCP>
      <RequiredCGMS>CGMS_NONE</RequiredCGMS>
    </WidevineContentKeySpec>
    <FairPlayPolicy persistent="false">
      <HDCPEnforcement>HDCP_NONE</HDCPEnforcement>
    </FairPlayPolicy>
    <License type="simple">
      <KeyId>{drm_key}</KeyId>
      <Policy>
        <Id>962c4b25-4c65-4b21-a6a3-fe2c7590053c</Id>
      </Policy>
      <Play>
        <Id>c7e7a2b0-87ad-4659-b59b-e5edf68bd5ea</Id>
      </Play>
    </License>
    <Policy id="962c4b25-4c65-4b21-a6a3-fe2c7590053c">
      <MinimumSecurityLevel>2000</MinimumSecurityLevel>
    </Policy>
    <Play id="c7e7a2b0-87ad-4659-b59b-e5edf68bd5ea">
      <OutputProtections>
        <OPL>
          <CompressedDigitalVideo>500</CompressedDigitalVideo>
          <UncompressedDigitalVideo>250</UncompressedDigitalVideo>
          <AnalogVideo>150</AnalogVideo>
        </OPL>
        <AnalogVideoExplicit>
          <Id ConfigData="1">C3FD11C6-F8B7-4D20-B008-1DB17D61F2DA</Id>
        </AnalogVideoExplicit>
      </OutputProtections>
    </Play>
    <KeyIDList>
      <KeyID>{drm_key}</KeyID>
    </KeyIDList>
    <Username>local</Username>
    <GenerationTime>2024-07-28 17:01:37.817</GenerationTime>
    <ExpirationTime>2024-07-28 17:11:37.817</ExpirationTime>
    <UniqueId>4dcdb908372d410cad01c0fc4120911e</UniqueId>
    <RSAPubKeyId>3c202c0ea50420870eb63e2412fa69f9</RSAPubKeyId>
  </Data>
  <Signature>kDDHB7xDVEbJMb6DucvdA0PxoeUslNn4AkqMq+kKMQQ/zATmjAYmE+iV8pcLanwPIp9kjKt6/RFcZuoYov8F2gWKfvaeSrxvBIMbjsmXpvoio61Kvl9GmnFkjh8KZxFDj23XxZ+dpCmoveUFSJvbq8VAsRqkCQGtpOJMzPdkdifE/TxmyIJXI0f6x5jPThpu/muqpaYLRCzpscbURx5vbU5kOSYDFcgEdL3jgoP4aOlM7p4mwo7FLyifNtqTNCP1+eKwIZf1ZkfhK7JHPFxOo7a//CaCaG52ER6amo2KloR+Vh1xWY4TPAiAj7VdxAac4Sp+AZpak79hdrpwZEDyig==</Signature>
</KeyOSAuthenticationXML>
    '''
    base64_custom_data = base64.b64encode(custom_data_xml.encode()).decode()
    headers = { 'Customdata': base64_custom_data }
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
