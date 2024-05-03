import time

from ..utils.download_video_nre import download_video_nre
from ..models.dl_request_platform import DLRequestPlatform
from ..models.dl_request import DLRequest

def GENERIC_MANIFEST_DL(dl_request: DLRequest):
  filename = time.strftime('%Y%m%d-%H%M%S')
  if dl_request.output_filename:
    filename = dl_request.output_filename

  download_video_nre(
    dl_request.video_page_or_manifest_url,
    filename,
    DLRequestPlatform.GENERIC_MANIFEST,
    dl_request.preferred_quality_matcher,
  )
