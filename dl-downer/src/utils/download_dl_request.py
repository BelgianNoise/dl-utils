import os
import shutil
import time
from loguru import logger
from ..models.dl_request_platform import DLRequestPlatform
from ..models.dl_request import DLRequest
from ..models.download_result import DownloadResult
from .apply_output_pattern import apply_output_pattern
from .parse_filename_fields import parse_filename_fields

def download_dl_request(
  dl_request: DLRequest,
):
  logger.info(f'Downloading {dl_request.video_page_or_manifest_url} from {dl_request.platform} ...')
  start_time = time.time()

  result: DownloadResult = None

  if dl_request.platform == DLRequestPlatform.VRTMAX.value:
    from ..downloaders.VRTMAX import VRTMAX_DL
    result = VRTMAX_DL(dl_request)
  elif dl_request.platform == DLRequestPlatform.GOPLAY.value:
    from ..downloaders.GOPLAY import GOPLAY_DL
    result = GOPLAY_DL(dl_request)
  elif dl_request.platform == DLRequestPlatform.VTMGO.value:
    from ..downloaders.VTMGO import VTMGO_DL
    result = VTMGO_DL(dl_request)
  elif dl_request.platform == DLRequestPlatform.STREAMZ.value:
    from ..downloaders.STREAMZ import STREAMZ_DL
    result = STREAMZ_DL(dl_request)
  elif dl_request.platform == DLRequestPlatform.GENERIC_MANIFEST.value:
    from ..downloaders.GENERIC_MANIFEST import GENERIC_MANIFEST_DL
    result = GENERIC_MANIFEST_DL(dl_request)
  elif dl_request.platform == DLRequestPlatform.YOUTUBE.value:
    from ..downloaders.YOUTUBE import YOUTUBE_DL
    result = YOUTUBE_DL(dl_request)
  else:
    logger.error(f'Unsupported platform: {dl_request.platform}')
    raise Exception('Unsupported platform')

  # Validate downloader result before proceeding
  if result is None:
    logger.error(f'Downloader returned no result for platform: {dl_request.platform}')
    raise RuntimeError('Download failed: no result returned from downloader')
  if not isinstance(result, DownloadResult):
    logger.error(f'Downloader returned unexpected result type for platform {dl_request.platform}: {type(result)}')
    raise TypeError('Download failed: unexpected downloader result type')
  if not getattr(result, 'file_path', None):
    logger.error(f'DownloadResult missing file_path for platform: {dl_request.platform}')
    raise ValueError('Download failed: missing file_path in downloader result')
  if not os.path.exists(result.file_path):
    logger.error(f'Downloaded file does not exist at expected path: {result.file_path}')
    raise FileNotFoundError(f'Download failed: file not found at {result.file_path}')

  # --- Centralized filename pattern logic ---
  title = dl_request.output_filename if dl_request.output_filename else result.title

  # Use explicitly returned season/episode if available.
  # Otherwise, attempt generic regex extraction from the suggested filename.
  season = result.season
  episode = result.episode
  if season is None or episode is None:
    parsed = parse_filename_fields(os.path.splitext(os.path.basename(result.suggested_filepath))[0])
    if season is None:
      season = parsed['season']
    if episode is None:
      episode = parsed['episode']

  final_path = apply_output_pattern(
    title=title,
    platform=result.platform,
    extension=result.extension,
    suggested_filepath=result.suggested_filepath,
    current_filepath=result.file_path,
    season=season,
    episode=episode,
  )

  # Copy + delete the file to the final location if it differs
  # (always copy+delete instead of shutil.move — move fails across filesystems)
  if os.path.abspath(result.file_path) != os.path.abspath(final_path):
    os.makedirs(os.path.dirname(final_path), exist_ok=True)
    shutil.copy2(result.file_path, final_path)
    os.remove(result.file_path)
    logger.info(f'Moved {result.file_path} → {final_path}')
  else:
    logger.debug(f'File already at final location: {final_path}')

  duration = time.time() - start_time
  logger.info(f'({duration:.2f}s) Downloaded to {final_path}')
