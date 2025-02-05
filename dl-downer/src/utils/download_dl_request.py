import time
from loguru import logger
from ..models.dl_request_platform import DLRequestPlatform
from ..models.dl_request import DLRequest

def download_dl_request(
  dl_request: DLRequest,
):
  logger.info(f'Downloading {dl_request.video_page_or_manifest_url} from {dl_request.platform} ...')
  start_time = time.time()

  if dl_request.platform == DLRequestPlatform.VRTMAX.value:
    from ..downloaders.VRTMAX import VRTMAX_DL
    VRTMAX_DL(dl_request)
  elif dl_request.platform == DLRequestPlatform.GOPLAY.value:
    from ..downloaders.GOPLAY import GOPLAY_DL
    GOPLAY_DL(dl_request)
  elif dl_request.platform == DLRequestPlatform.VTMGO.value:
    from ..downloaders.VTMGO import VTMGO_DL
    VTMGO_DL(dl_request)
  elif dl_request.platform == DLRequestPlatform.GENERIC_MANIFEST.value:
    from ..downloaders.GENERIC_MANIFEST import GENERIC_MANIFEST_DL
    GENERIC_MANIFEST_DL(dl_request)
  elif dl_request.platform == DLRequestPlatform.YOUTUBE.value:
    from ..downloaders.YOUTUBE import YOUTUBE_DL
    YOUTUBE_DL(dl_request)
  else:
    logger.error(f'Unsupported platform: {dl_request.platform}')
    # throw error for now
    raise Exception('Unsupported platform')

  duration = time.time() - start_time
  logger.info(f'({duration:.2f}s) Downloaded {dl_request.video_page_or_manifest_url} from {dl_request.platform} successfully!')
