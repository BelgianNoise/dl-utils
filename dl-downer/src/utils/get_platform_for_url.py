from ..models.dl_request_platform import DLRequestPlatform

def get_platform_for_url(url: str) -> DLRequestPlatform:
  if 'vrt.be' in url:
    return DLRequestPlatform.VRTMAX.value
  if 'goplay.be' in url:
    return DLRequestPlatform.GOPLAY.value
  if 'vtmgo.be' in url:
    return DLRequestPlatform.VTMGO.value
  return DLRequestPlatform.UNKNOWN
