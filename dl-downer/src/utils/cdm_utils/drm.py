import base64
import re
import requests
from typing import NamedTuple, Optional

from loguru import logger

from .local_cdm import Local_CDM
from .local_playready_cdm import Local_PlayReady_CDM

DEFAULT_DRM_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'

DRM_PROVIDER_ALIASES = {
  'playready': [
    'com.microsoft.playready',
    'com.microsoft.playready.recommendation',
    'playready',
  ],
  'widevine': ['com.widevine.alpha', 'widevine'],
}

DRM_PROVIDER_TO_UUID = {
  'com.microsoft.playready': '9a04f079-9840-4286-ab92-e65be0885f95',
  'com.microsoft.playready.recommendation': '9a04f079-9840-4286-ab92-e65be0885f95',
  'playready': '9a04f079-9840-4286-ab92-e65be0885f95',
  'com.widevine.alpha': 'edef8ba9-79d6-4ace-a3c8-27dcd51d21ed',
  'widevine': 'edef8ba9-79d6-4ace-a3c8-27dcd51d21ed',
}

WIDEVINE_PROVIDERS = {
  'com.widevine.alpha',
  'widevine',
}

PLAYREADY_PROVIDERS = {
  'com.microsoft.playready',
  'com.microsoft.playready.recommendation',
  'playready',
}


class PsshInfo(NamedTuple):
  pssh: str
  license_url: Optional[str]


def get_license_url_from_playready_object(playready_object_b64: str) -> str:
  """Decode a base64 PlayReady Object (PRO) and extract LA_URL."""
  try:
    wrm_header_like = base64.b64decode(playready_object_b64).decode('utf-16le', errors='ignore')
  except Exception as e:
    raise Exception(f'Invalid base64 PlayReady object: {e}')

  match = re.search(r'<LA_URL>([^<]+)</LA_URL>', wrm_header_like, flags=re.IGNORECASE)
  if not match:
    raise Exception('No LA_URL found in PlayReady object')

  return match.group(1).strip()


def extract_dash_stream_info(streams, drm_system='playready') -> dict:
  """Extract DASH stream and DRM details from a streams list."""
  dash_stream = None
  for stream in streams:
    if stream['type'] == 'dash':
      dash_stream = stream
      break
  assert dash_stream, 'No dash stream found'

  drm_entries = dash_stream.get('drm', {})
  preferred_keys = DRM_PROVIDER_ALIASES.get(drm_system, [drm_system])

  drm_data = None
  drm_provider = None
  for key in preferred_keys:
    if key in drm_entries:
      drm_data = drm_entries[key]
      drm_provider = key
      break

  assert drm_data, f'No {drm_system} drm entry found in stream config. Available: {list(drm_entries.keys())}'

  return {
    'mpd_url': dash_stream['url'],
    'license_url': drm_data['licenseUrl'],
    'auth_token': drm_data.get('drmtoday', {}).get('authToken'),
    'drm_provider': drm_provider,
  }


def get_pssh_from_manifest(mpd_url, drm_provider='com.microsoft.playready', request_headers=None) -> PsshInfo:
  """Extract a DRM-provider specific PSSH and optional license URL from an MPD manifest."""
  manifest_response = requests.get(mpd_url, headers=request_headers)
  manifest_response.raise_for_status()
  logger.debug(f'Manifest response status: {manifest_response.status_code}')

  drm_uuid = DRM_PROVIDER_TO_UUID.get(drm_provider)
  assert drm_uuid, f'Unsupported drm provider: {drm_provider}'

  try:
    cp_pattern = (
      rf'<ContentProtection[^>]*schemeIdUri="urn:uuid:{re.escape(drm_uuid)}"[^>]*>'
      rf'.*?</ContentProtection>'
    )
    cp_matches = re.findall(cp_pattern, manifest_response.text, flags=re.IGNORECASE | re.DOTALL)
    cp_block = cp_matches[0]

    pssh_matches = re.findall(r'<cenc:pssh[^>]*>([^<]+)</cenc:pssh>', cp_block, flags=re.IGNORECASE | re.DOTALL)
    pssh = pssh_matches[0].strip()
    assert pssh

    license_url = None
    if drm_provider in PLAYREADY_PROVIDERS:
      pro_matches = re.findall(r'<(?:mspr:)?pro[^>]*>([^<]+)</(?:mspr:)?pro>', cp_block, flags=re.IGNORECASE | re.DOTALL)
      if pro_matches:
        try:
          license_url = get_license_url_from_playready_object(pro_matches[0].strip())
        except Exception as e:
          logger.debug(f'Failed to extract PlayReady LA_URL from PRO: {e}')

    return PsshInfo(pssh=pssh, license_url=license_url)
  except Exception:
    raise Exception(f'Failed to find {drm_provider} pssh in manifest: {manifest_response.text}')


def get_widevine_keys(
  pssh,
  license_url,
  auth_token,
  origin_url=None,
  ua=DEFAULT_DRM_USER_AGENT,
  custom_headers=None,
):
  """Get Widevine decryption keys."""
  cdm = Local_CDM()
  challenge = cdm.generate_challenge(pssh)
  headers = {
    'connection': 'keep-alive',
    'accept': '*/*',
    'accept-encoding': 'gzip, deflate, br',
  }
  if origin_url:
    headers['origin'] = origin_url
  headers['user-agent'] = ua
  if auth_token:
    headers['X-Dt-Auth-Token'] = auth_token
  if custom_headers:
    headers.update(custom_headers)

  license_response = requests.post(license_url, data=challenge, headers=headers)
  license_response.raise_for_status()

  content_type = license_response.headers.get('content-type', '').lower()
  if 'json' in content_type:
    license_response_json = license_response.json()
    license = license_response_json.get('license', license_response.content)
  else:
    try:
      license_response_json = license_response.json()
      license = license_response_json.get('license', license_response.content)
    except Exception:
      license = license_response.content

  logger.debug(f'License: {license}')
  keys = cdm.parse_license(license)
  cdm.close()
  return keys


def get_playready_keys(pssh, license_url, auth_token, origin_url=None, ua=DEFAULT_DRM_USER_AGENT, custom_headers=None):
  """Get PlayReady decryption keys."""
  cdm = Local_PlayReady_CDM()
  challenge = cdm.generate_challenge(pssh)
  headers = {
    'connection': 'keep-alive',
    'accept': '*/*',
    'accept-encoding': 'gzip, deflate, br',
  }
  if origin_url:
    headers['origin'] = origin_url
  headers['user-agent'] = ua
  if auth_token:
    headers['X-Dt-Auth-Token'] = auth_token
  if custom_headers:
    headers.update(custom_headers)

  if isinstance(challenge, str):
    headers.setdefault('Content-Type', 'text/xml; charset=UTF-8')

  license_response = requests.post(license_url, data=challenge, headers=headers)
  license_response.raise_for_status()

  content_type = license_response.headers.get('content-type', '').lower()
  if 'json' in content_type:
    license_response_json = license_response.json()
    license = license_response_json.get('license', license_response.text)
  else:
    license = license_response.text

  logger.debug(f'License: {license}')
  keys = cdm.parse_license(license)
  cdm.close()
  return keys


def get_decryption_keys(
  pssh,
  license_url,
  auth_token,
  drm_provider,
  origin_url=None,
  ua=DEFAULT_DRM_USER_AGENT,
  custom_headers=None,
):
  """Get decryption keys for the selected DRM provider."""
  if drm_provider in WIDEVINE_PROVIDERS:
    return get_widevine_keys(
      pssh,
      license_url,
      auth_token,
      origin_url,
      ua,
      custom_headers,
    )

  if drm_provider in PLAYREADY_PROVIDERS:
    return get_playready_keys(pssh, license_url, auth_token, origin_url, ua, custom_headers)

  raise Exception(f'Unsupported drm provider for this downloader: {drm_provider}')
