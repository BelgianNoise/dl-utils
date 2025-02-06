import os
import traceback
from loguru import logger
from .models.dl_request import DLRequest
from .models.dl_request_platform import DLRequestPlatform
from .utils.download_dl_request import download_dl_request
from .utils.validate_server_structure import validate_server_structure
from .utils.get_platform_for_url import get_platform_for_url

def do_the_download_thing(url: str):
  platform = get_platform_for_url(url)
  dl_request = DLRequest('-', '-', platform, url, '-', '-', None, 'best')
  try:
    download_dl_request(dl_request)
  except Exception as e:
    logger.error(f'An error occurred: {e}')
    logger.error(traceback.format_exc())

def handle_cli():
  validate_server_structure()
  from dotenv import load_dotenv
  load_dotenv()

  # Read first cli parameter if exists
  args_length = len(os.sys.argv)
  if args_length < 2:
    logger.error('No URL provided. Example usage: python3 cli.py https://www.vrt.be/vrtmax/a-z/-likeme/5/-likeme-s5a1/')
    return
  url = os.sys.argv[1]
  do_the_download_thing(url)
