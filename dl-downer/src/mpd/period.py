import os
import shutil
import uuid
import xml.etree.ElementTree as ET

from typing import List
from loguru import logger

from .adaptation_set import AdaptationSet
from .mpd_utils import transform_mpd_time_to_milisecondsseconds
from .mpd_download_options import MPDDownloadOptions
from ..utils.files import merge_files

class Period:
  def __init__(
    self,
    id: str,
    start: int = None,
    duration: int = None,
    base_url: str = None,
    adaptation_sets: List[AdaptationSet] = [],
  ):
    self.id = id
    self.start = start
    self.duration = duration
    self.base_url = base_url
    self.adaptation_sets = adaptation_sets
  def __str__(self):
    return f'<Period(id={self.id}, start={self.start}, duration={self.duration})>'
  def __repr__(self):
    return self.__str__()

  @staticmethod
  def from_element(el: ET.Element) -> 'Period':
    logger.debug(f'Parsing Period with id: {el.get("id")}')
    adaptation_sets = []
    for adaptation in el.findall('AdaptationSet'):
      adaptation_sets.append(AdaptationSet.from_element(adaptation))

    base_url = None
    base_url_el = el.find('BaseURL')
    if base_url_el is not None:
      base_url = base_url_el.text

    return Period(
      id=el.get('id'),
      start=transform_mpd_time_to_milisecondsseconds(el.get('start')) if el.get('start') is not None else None,
      duration=transform_mpd_time_to_milisecondsseconds(el.get('duration')) if el.get('duration') is not None else None,
      base_url=base_url,
      adaptation_sets=adaptation_sets,
    )
  
  def download(
    self,
    tmp_dir: str,
    base_url: str,
    download_options: MPDDownloadOptions = None,
  ) -> str:
    ''':return: the path to the downloaded period mp4 file'''
    logger.debug(f'Downloading period {self.id}')
    # Create a temporary folder
    my_uuid = str(uuid.uuid4())[:8]
    my_tmp_dir = os.path.join(tmp_dir, f'period-{my_uuid}')
    os.makedirs(my_tmp_dir, exist_ok=True)

    # Keep track of all files that need to be merged
    files_to_merge = []

    # Find audio adaptation sets
    audio_adaptation_sets = list(filter(lambda adaptation_set: adaptation_set.mime_type.startswith('audio/'), self.adaptation_sets))
    # Download all audio streams
    for audio_adaptation_set in audio_adaptation_sets:
      audio_file = audio_adaptation_set.download(my_tmp_dir, base_url, download_options)
      if audio_file is not None:
        files_to_merge.append(audio_file)
    
    # Find video adaptation sets
    video_adaptation_sets = list(filter(lambda adaptation_set: adaptation_set.mime_type.startswith('video/'), self.adaptation_sets))
    # Download all video streams
    for video_adaptation_set in video_adaptation_sets:
      video_file = video_adaptation_set.download(my_tmp_dir, base_url, download_options)
      if video_file is not None:
        files_to_merge.append(video_file)

    # merge audio and video files
    merged_file = os.path.join(my_tmp_dir, f'merged-{my_uuid}.mp4')
    merge_files(files_to_merge, merged_file)
    # move the merged file to the tmp_dir
    out_file = os.path.join(tmp_dir, os.path.basename(merged_file))
    shutil.move(merged_file, out_file)

    # Delete own tmp folder
    shutil.rmtree(my_tmp_dir)

    logger.debug(f'Downloaded period {self.id} to {out_file}')
    return out_file
