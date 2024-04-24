import json
import re
import os
import shutil
import requests

from loguru import logger

from ..mpd.mpd import MPD
from ..mpd.mpd_download_options import MPDDownloadOptions
from ..utils.filename import parse_filename
from ..models.dl_request import DLRequest

def GOPLAY_DL(dl_request: DLRequest):

  # Parse video uuid from the page
  page_resp = requests.get(dl_request.video_page_or_manifest_url)
  page_content = page_resp.text
  obj_string = re.search(r'<div data-hero="(.+?)"', page_content).group(1)
  obj_string = re.sub(r'&quot;', '"', obj_string)
  obj = json.loads(obj_string)
  for playlist in obj['data']['playlists']:
    for episode in playlist['episodes']:
      if episode['pageInfo']['url'] == dl_request.video_page_or_manifest_url.split('#')[0]:
        video_uuid = episode['videoUuid']
        type_form = episode['type']
        type_form = re.sub('_', '-', type_form)
        is_drm = episode['isDrm']
        if dl_request.output_filename is None:
          title = episode['pageInfo']['title']
          title = parse_filename(title)
        else:
          title = dl_request.output_filename
        break
  logger.debug(f'Video uuid: {video_uuid}')
  logger.debug(f'Type: {type_form}')
  logger.debug(f'Is DRM: {is_drm}')
  logger.debug(f'Title: {title}')

  # get video data
  video_data_url = f'https://api.goplay.be/web/v1/videos/{type_form}/{video_uuid}'
  logger.debug(f'Video data URL: {video_data_url}')
  video_data_resp = requests.get(
    video_data_url,
    headers={
      'authorization': 'Bearer eyJraWQiOiJCSHZsMjdjNzdGR2J5YWNyTk8xXC9yWXBPTjlzMFFPbjhtUTdzQnA5eCtvbz0iLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiIxZDI2YzhjMC04YjkyLTRkMzgtOTJjNC0yMWNlZjliODViY2UiLCJiaXJ0aGRhdGUiOiI5XC8xMFwvMTk5OCAiLCJnZW5kZXIiOiJtIiwiaXNzIjoiaHR0cHM6XC9cL2NvZ25pdG8taWRwLmV1LXdlc3QtMS5hbWF6b25hd3MuY29tXC9ldS13ZXN0LTFfZFZpU3NLTTVZIiwiY3VzdG9tOnBvc3RhbF9jb2RlIjoiMzAwMCIsImN1c3RvbTptaWdyYXRlZF91c2VyIjoiMCIsImN1c3RvbTpzdHJlZXRfYm94IjoiMDMiLCJjdXN0b206c2JzX2NvbmZpcm1lZF92aWVyIjoiMSIsImN1c3RvbTpwaG9uZSI6IjA0NzkzMTUxOTYiLCJjdXN0b206c2JzX2NvbmZpcm1lZF96ZXMiOiI2NjkiLCJjdXN0b206c2VsbGlnZW50SWQiOiIxMjU5NzIwIiwiYXV0aF90aW1lIjoxNzEzNjU0ODkwLCJleHAiOjE3MTM5NjMwNzEsImlhdCI6MTcxMzk1OTQ3MSwiZW1haWwiOiJraW5nLmFydGh1cjM2MEBnbWFpbC5jb20iLCJjdXN0b206YWNjb3VudF9jb25zZW50Ijoie1wiYWNjZXB0ZWRcIjp0cnVlLFwiZGF0ZVwiOjE3MDYyOTI3MzZ9IiwiY3VzdG9tOnN0cmVldF9udW1iZXIiOiIxNCIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJhZGRyZXNzIjp7ImZvcm1hdHRlZCI6IkRpZXN0c2VzdHJhYXQifSwicGhvbmVfbnVtYmVyX3ZlcmlmaWVkIjpmYWxzZSwiY29nbml0bzp1c2VybmFtZSI6IjFlNzI2NDdjOTE0ZTRkYzc2YzdlNzc5MWJjMDU0Mjg4ZjgzYTU0ZjQ2NmJkZGVhNTUwOGQ0NTFjZmNmZjBmYzAiLCJjdXN0b206Y2l0eSI6IkxldXZlbiIsImF1ZCI6IjZzMWg4NTFzOHVwbGNvNWg2bXFoMWphYzhtIiwiZXZlbnRfaWQiOiJkMzg1ZDZkZS1mOWQzLTRlNTUtYWVkNC1iZDQyYmQ3YTIxMjgiLCJ0b2tlbl91c2UiOiJpZCIsIm5hbWUiOiJBcnRodXIiLCJmYW1pbHlfbmFtZSI6IkpvcHBhcnQifQ.iFKYt5HDav28EtFQC57aiuhrXG8bvo8st33isvd9aRWkkeexGn_ZRk0ocFHUskZmpPxLUahliheAZnfm4-owM6IvLDn82Jj8BU__HMoZqsalmfNNpjWBS768rUs24p70xz0BuDFFiMur9Nuyt-ylQ346Tmcs5QgMCSzx3eMJYrhzAyhTc-cY24QhEwhSlmGacZ8jCYnkABVg26tWXwPCWmLgoNIat_PEUrabIPCPkeGOLTLSRPyPh4ZYH1lnpdhqxI19f_AwjPiMY3O7iGdgwbmzljOTOybfKxQBr535qtMIWznaBHsfbdsFsLJnyoYGrvwgn52DeF-9Ve4nGm7Jfw',
    },
  )
  if video_data_resp.status_code != 200:
    logger.debug(video_data_resp.text)
  video_data = video_data_resp.json()
  content_source_id = video_data['ssai']['contentSourceID']
  logger.debug(f'Content source ID: {content_source_id}')
  video_id = video_data['ssai']['videoID']
  logger.debug(f'Video ID: {video_id}')

  # get video streams
  streams_resp = requests.post(f'https://dai.google.com/ondemand/dash/content/{content_source_id}/vid/{video_id}/streams')
  streams = streams_resp.json()
  stream_manifest = streams['stream_manifest']
  logger.debug(f'Stream manifest: {stream_manifest}')
  
  if is_drm:
    # do key shenanigans later
    raise Exception('DRM protected content not supported yet')
  
  mpd = MPD.from_url(stream_manifest)
  download_options = MPDDownloadOptions()
  # set the preferred quality matcher
  if dl_request.preferred_quality_matcher:
    download_options.video_resolution = dl_request.preferred_quality_matcher
  # download the mpd
  final_file = mpd.download('./tmp', download_options)
  # move the final file to the downloads folder
  save_dir = os.getenv('DOWNLOADS_FOLDER', './downloads')
  if not save_dir.endswith('/'):
    save_dir += '/'
  save_dir += dl_request.platform
  shutil.move(final_file, os.path.join(save_dir, title + '.mp4'))
  logger.debug(f'Downloaded {title} to {save_dir}')

