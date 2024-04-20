from http.cookiejar import Cookie
import json
import os
from typing import List
from loguru import logger

def get_cookie_file_path(service: str):
  ''' Get the path to the cookie file depending on the service'''

  cookiePath = os.getenv('COOKIES_FOLDER', './cookies')
  # add "/" at the end if not already there
  if not cookiePath.endswith('/'):
    cookiePath += '/'
  cookiePath += f'{service}.json'

  return cookiePath

def save_cookies(service: str, cookies: List[Cookie]):
  ''' Write cookies to a file'''

  cookiePath = get_cookie_file_path(service)
  with open(cookiePath, 'w') as f:
    json.dump(cookies, f, indent=2)
  
  logger.debug(f'Saved {len(cookies)} cookies to {service}')

def get_cookies(service: str) -> List[Cookie]:
  ''' Read cookies from a file'''

  cookiePath = get_cookie_file_path(service)
  if not os.path.exists(cookiePath):
    logger.debug(f'No cookies found for {service}')
    return []

  with open(cookiePath, 'r') as f:
    cookies = json.load(f)
  
  logger.debug(f'Loaded {len(cookies)} cookies from {service}')
  return cookies
