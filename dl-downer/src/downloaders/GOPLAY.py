import json
import re
import os
import time
import requests
import concurrent.futures
import xml.etree.ElementTree as ET

from loguru import logger

from ..utils.merge_video_audio import merge_video_audio
from ..utils.concat_files import concat_files
from ..utils.mpd_tree import get_all_audio_streams, get_all_video_streams
from ..utils.filename import parse_filename
from ..utils.download_video import download_video
from ..models.dl_request_platform import DLRequestPlatform
from ..models.dl_request import DLRequest

def goplay_non_drm_audio(
  root: ET.Element,
  my_tmp_dir: str,
) -> str:
  '''
  Download and concatanate all audio streams

  :returns: Path to concatanated audio file
  '''
  # list all available video streams
  audio_streams_root = get_all_audio_streams(root)
  logger.debug(f'Available audio streams: {audio_streams_root}')

  first = audio_streams_root[0]
  last = audio_streams_root[-1]
  total_segments = last.start_number + last.segments - first.start_number
  # Do some toomfoolery cause goplay's mpd files don't make sense
  main_audio_stream = first.copy()
  main_audio_stream.segments = total_segments
  
  audio_streams = []
  # split into 2 groups
  # - 2 groups cause this is supposed to run on a single core
  #   + python usually only runs on a single core
  group_size = (total_segments//2)+1
  for i in range(0, main_audio_stream.segments, group_size):
    ss = main_audio_stream.copy()
    ss.start_number = i
    ss.segments = group_size-1 if i + group_size-1 < total_segments else total_segments - ss.start_number
    audio_streams.append(ss)

  # get the tmp_dir for the audio stream
  audio_tmp_dir = main_audio_stream.get_tmp_dir()
  # get the initialization segment
  init_filename = main_audio_stream.download_init(audio_tmp_dir)

  start_time = time.time()

  # for every audio stream, download the segments
  with concurrent.futures.ThreadPoolExecutor() as executor:
    download_tasks = [executor.submit(audio_stream.download_segments, audio_tmp_dir) for audio_stream in audio_streams]
    for task in concurrent.futures.as_completed(download_tasks):
      try:
        task.result()
      except Exception as e:
        logger.error(f"Error occurred during audio stream download: {str(e)}")
        raise e

  logger.info(f'Audio download time: {time.time() - start_time}')

  main_audio_stream.add_segments_to_init(init_filename)
  output_filename = main_audio_stream.finalize_init(init_filename, my_tmp_dir)
  main_audio_stream.cleanup_tmp_dir()
  return output_filename


def goplay_non_drm_video(
  root: ET.Element,
  my_tmp_dir: str,
  preferred_quality_matcher: str,
) -> str:
  # list all available video streams
  video_streams_unfiltered = get_all_video_streams(root)
  logger.debug(f'Available video streams: {video_streams_unfiltered}')

  # select streams based on preferred quality
  video_streams = []
  preferred_height = '1080'
  if preferred_quality_matcher:
    preferred_height = preferred_quality_matcher

  logger.debug(f'Finding video streams with height: {preferred_height}')
  for stream in video_streams_unfiltered:
    if stream.height == int(preferred_height):
      video_streams.append(stream)
  # if none were found, select best quality
  if len(video_streams) == 0:
    logger.debug(f'No video stream found with height: {preferred_height} | selecting best quality stream')
    best_height = 0
    for stream in video_streams_unfiltered:
      if stream.height > best_height:
        best_height = stream.height
    logger.debug(f'Best height selected: {best_height}')
    for stream in video_streams_unfiltered:
      if stream.height == best_height:
        video_streams.append(stream)
  if len(video_streams) == 0:
    logger.error('No video streams found')
    raise Exception('No video streams found')
  logger.debug(f'Selected video streams: {video_streams}')

  first = video_streams[0]
  last = video_streams[-1]
  total_segments = last.start_number + last.segments - first.start_number
  # Do some toomfoolery cause goplay's mpd files don't make sense
  main_video_stream = first.copy()
  main_video_stream.segments = total_segments
  
  video_streams = []
  # split into 2 groups
  # - 2 groups cause this is supposed to run on a single core
  #   + python usually only runs on a single core
  group_size = (total_segments//2)+1
  for i in range(0, main_video_stream.segments, group_size):
    ss = main_video_stream.copy()
    ss.start_number = i
    ss.segments = group_size-1 if i + group_size-1 < total_segments else total_segments - ss.start_number
    video_streams.append(ss)

  # get the tmp_dir for the video stream
  video_tmp_dir = main_video_stream.get_tmp_dir()
  # get the initialization segment
  init_filename = main_video_stream.download_init(video_tmp_dir)

  start_time = time.time()

  # for every audio stream, download the segments
  with concurrent.futures.ThreadPoolExecutor() as executor:
    download_tasks = [executor.submit(video_stream.download_segments, video_tmp_dir) for video_stream in video_streams]
    for task in concurrent.futures.as_completed(download_tasks):
      try:
        task.result()
      except Exception as e:
        logger.error(f"Error occurred during video stream download: {str(e)}")
        raise e

  logger.info(f'Video download time: {time.time() - start_time}')

  main_video_stream.add_segments_to_init(init_filename)
  output_filename = main_video_stream.finalize_init(init_filename, my_tmp_dir)
  main_video_stream.cleanup_tmp_dir()
  return output_filename

def goplay_non_drm(
  dl_request: DLRequest,
  stream_manifest: str,
  title: str,
):
  # Get mpd content
    mpd_request = requests.get(stream_manifest)
    mpd_content = mpd_request.text
    mpd_content = re.sub(r'xmlns="(.*?)"', '', mpd_content)
    # parse content as XML
    root = ET.fromstring(mpd_content)
    # print base url
    base_url = root.find('BaseURL').text
    logger.debug(f'Base URL: {base_url}')

    tmp_dir = f'./tmp/{title}'
    os.makedirs(tmp_dir, exist_ok=True)

    audio_file = goplay_non_drm_audio(root, tmp_dir)
    video_file = goplay_non_drm_video(root, tmp_dir, dl_request.preferred_quality_matcher)

    # merge audio and video files
    merged_filename = f'./tmp/{title}.mp4'
    merge_video_audio(video_file, audio_file, merged_filename)

    # remove tmp dir
    import shutil
    shutil.rmtree(tmp_dir)
    
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
      'authorization': 'Bearer eyJraWQiOiJCSHZsMjdjNzdGR2J5YWNyTk8xXC9yWXBPTjlzMFFPbjhtUTdzQnA5eCtvbz0iLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiIxZDI2YzhjMC04YjkyLTRkMzgtOTJjNC0yMWNlZjliODViY2UiLCJiaXJ0aGRhdGUiOiI5XC8xMFwvMTk5OCAiLCJnZW5kZXIiOiJtIiwiaXNzIjoiaHR0cHM6XC9cL2NvZ25pdG8taWRwLmV1LXdlc3QtMS5hbWF6b25hd3MuY29tXC9ldS13ZXN0LTFfZFZpU3NLTTVZIiwiY3VzdG9tOnBvc3RhbF9jb2RlIjoiMzAwMCIsImN1c3RvbTptaWdyYXRlZF91c2VyIjoiMCIsImN1c3RvbTpzdHJlZXRfYm94IjoiMDMiLCJjdXN0b206c2JzX2NvbmZpcm1lZF92aWVyIjoiMSIsImN1c3RvbTpwaG9uZSI6IjA0NzkzMTUxOTYiLCJjdXN0b206c2JzX2NvbmZpcm1lZF96ZXMiOiI2NjkiLCJjdXN0b206c2VsbGlnZW50SWQiOiIxMjU5NzIwIiwiYXV0aF90aW1lIjoxNzEzNjU0ODkwLCJleHAiOjE3MTM3ODM4NTUsImlhdCI6MTcxMzc4MDI1NSwiZW1haWwiOiJraW5nLmFydGh1cjM2MEBnbWFpbC5jb20iLCJjdXN0b206YWNjb3VudF9jb25zZW50Ijoie1wiYWNjZXB0ZWRcIjp0cnVlLFwiZGF0ZVwiOjE3MDYyOTI3MzZ9IiwiY3VzdG9tOnN0cmVldF9udW1iZXIiOiIxNCIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJhZGRyZXNzIjp7ImZvcm1hdHRlZCI6IkRpZXN0c2VzdHJhYXQifSwicGhvbmVfbnVtYmVyX3ZlcmlmaWVkIjpmYWxzZSwiY29nbml0bzp1c2VybmFtZSI6IjFlNzI2NDdjOTE0ZTRkYzc2YzdlNzc5MWJjMDU0Mjg4ZjgzYTU0ZjQ2NmJkZGVhNTUwOGQ0NTFjZmNmZjBmYzAiLCJjdXN0b206Y2l0eSI6IkxldXZlbiIsImF1ZCI6IjZzMWg4NTFzOHVwbGNvNWg2bXFoMWphYzhtIiwiZXZlbnRfaWQiOiJkMzg1ZDZkZS1mOWQzLTRlNTUtYWVkNC1iZDQyYmQ3YTIxMjgiLCJ0b2tlbl91c2UiOiJpZCIsIm5hbWUiOiJBcnRodXIiLCJmYW1pbHlfbmFtZSI6IkpvcHBhcnQifQ.RBdNyBHE3yiUyUxNJau_RzQk8H8k51RE3x-iUjYm92uajHkgNhjz3wi8WFcwJWDbfa8A3MYm1L4fpDdEGTnzLD-kK_Ln1TToh2LPePWbsq8uSENpKvOcuczxhmkmvC-w8MtZL1AMutF1A64RESRQ45wFowZN-IFE1vwbAUVXKKWt70nsvFfTzvOxzNgWsi5oSBXibKMBR5Qt9cGP8Gf1ur-JT8hOzRj62al5DmEQPBhaRe60oEKj673UsLSnupzp3hzHJFIW1AYlfJSgY6W2nD70G7xhxNJZDH49pY9AgspjKm60d1CG_5viAMQnh05VQWx9P6yFvBz_Jicu3MBcaw',
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
    download_video(
      stream_manifest,
      title,
      DLRequestPlatform[dl_request.platform],
      dl_request.preferred_quality_matcher,
    )
  else:
    goplay_non_drm(
      dl_request,
      stream_manifest,
      title,
    )
