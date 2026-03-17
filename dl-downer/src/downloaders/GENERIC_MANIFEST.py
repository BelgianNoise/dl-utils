import time

from ..utils.download_video_nre import download_video_nre
from ..utils.filename import parse_filename
from ..models.dl_request_platform import DLRequestPlatform
from ..models.dl_request import DLRequest
from ..models.download_result import DownloadResult

def GENERIC_MANIFEST_DL(dl_request: DLRequest) -> DownloadResult:
  title = dl_request.output_filename if dl_request.output_filename else time.strftime('%Y%m%d-%H%M%S')

  downloaded_file = download_video_nre(
    dl_request.video_page_or_manifest_url,
    parse_filename(title),
    DLRequestPlatform.GENERIC_MANIFEST,
    dl_request.preferred_quality_matcher,
  )

  return DownloadResult(
    file_path=downloaded_file,
    title=title,
    platform=DLRequestPlatform.GENERIC_MANIFEST.value,
    extension='mkv',
    suggested_filepath=downloaded_file,
  )
