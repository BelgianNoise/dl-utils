import os
import shutil
import urllib
import uuid
import requests
import re
from loguru import logger
from typing import List
import xml.etree.ElementTree as ET

from .period import Period
from .mpd_download_options import MPDDownloadOptions
from ..utils.files import concat_files, merge_files, convert_to_mkv

class MPD:
  def __init__(
    self,
    base_url: str = None,
    periods: List[Period] = [],
  ):
    self.base_url = base_url
    self.periods = periods
  def __str__(self):
    return f'<MPD(base_url={self.base_url}, periods={self.periods})>'
  def __repr__(self):
    return self.__str__()

  @staticmethod
  def from_element(el: ET.Element) -> 'MPD':
    base_url = None
    # look globally for BaseURL
    base_url_el = el.find('.//BaseURL')
    if base_url_el is not None:
      base_url = base_url_el.text

    periods = []
    for period in el.findall('Period'):
      periods.append(Period.from_element(period))
    
    return MPD(
      base_url=base_url,
      periods=periods,
    )
  
  @staticmethod
  def from_string(mpd_string: str) -> 'MPD':
    mpd_string = re.sub(r'xmlns=".*?"', '', mpd_string)
    root_xml = ET.fromstring(mpd_string)
    return MPD.from_element(root_xml)
  
  @staticmethod
  def from_url(mpd_url: str) -> 'MPD':
    # cut off fragment
    mpd_url = mpd_url.split('#')[0]
    # cut off query params
    mpd_url = mpd_url.split('?')[0]
    mpd_response = requests.get(mpd_url)
    mpd_string = mpd_response.text
    mpd = MPD.from_string(mpd_string)
    # set base_url
    if mpd.base_url is None:
      logger.debug(f'No base_url found in MPD, using MPD URL as base_url')
      mpd.base_url = mpd_url
    elif not mpd.base_url.startswith('http'):
      logger.debug(f'Base URL is relative, joining with MPD URL')
      mpd.base_url = urllib.parse.urljoin(mpd_url, mpd.base_url)
    else:
      logger.debug(f'Base URL is absolute, using as is')
    return mpd
  
  def download(
    self,
    tmp_dir: str,
    download_options: MPDDownloadOptions = None,
  ) -> str:
    '''Downloads all periods and concatenates them into one file'''

    logger.debug(f'Downloading MPD {self.base_url} with options {download_options}')
    # Create a temporary folder
    my_uuid = str(uuid.uuid4())[:8]
    my_tmp_dir = os.path.join(tmp_dir, f'mpd-{my_uuid}')
    os.makedirs(my_tmp_dir, exist_ok=True)
    # download all periods
    period_download_results = []

    for period in self.periods:

      ignore_period = False
      if download_options is not None:
        for ignore_period_regex in download_options.ignore_periods:
          if re.match(ignore_period_regex, period.id):
            ignore_period = True
            break

      if ignore_period is True:
        logger.debug(f'Ignoring period {period.id}')
        continue

      period_download_result = period.download(my_tmp_dir, self.base_url, download_options)
      period_download_results.append(period_download_result)

    if len(period_download_results) == 0:
      raise Exception(f'No periods were downloaded {self.periods}')
    
    # validate period_download_results should be a list[List[str]]
    if not all(isinstance(period_download_result, list) for period_download_result in period_download_results):
      raise Exception(f'Expected period_download_results to be a list of lists, got {period_download_results}')

    if download_options.merge_method == 'period':
      # simply concat all periods

      # some manifests will have multiple periods, in that case we need to concat them
      created_file = period_download_results[0]
      # concat all files
      if len(period_download_results) > 1:
        created_file = os.path.join(my_tmp_dir, f'combined-periods-{my_uuid}.mp4')
        # All elements of the list should be of length 1
        if not all(len(period_download_result) == 1 for period_download_result in period_download_results):
          raise Exception(f'Expected period_download_results to be a list of lists with length 1, got {period_download_results}')
        # lambda to get all first elements of the sublists
        files_to_merge = list(map(lambda x: x[0], period_download_results))
        concat_files(files_to_merge, created_file)
    elif download_options.merge_method == 'format':
      if len(period_download_results) < 1:
        raise Exception(f'Expected at least one period to be downloaded, got {period_download_results}')
      # All elements of the list should be of length 2
      if not all(len(period_download_result) == 2 for period_download_result in period_download_results):
        raise Exception(f'Expected period_download_results to be a list of lists with length 2, got {period_download_results}')
      # lambda to get all first elements of the sublists
      audio_files_to_merge = list(map(lambda x: x[0], period_download_results))
      # lambda to get all second elements of the sublists
      video_files_to_merge = list(map(lambda x: x[1], period_download_results))
      # merge audio files
      audio_file = audio_files_to_merge[0]
      if len(audio_files_to_merge) > 1:
        audio_file = os.path.join(my_tmp_dir, f'audio-{my_uuid}.mp4')
        concat_files(audio_files_to_merge, audio_file)
      # merge video files
      video_file = video_files_to_merge[0]
      if len(video_files_to_merge) > 1:
        video_file = os.path.join(my_tmp_dir, f'video-{my_uuid}.mp4')
        concat_files(video_files_to_merge, video_file)
      # merge audio and video files
      created_file = os.path.join(my_tmp_dir, f'merged-formats-{my_uuid}.mp4')
      merge_files([audio_file, video_file], created_file)
    else:
      raise Exception(f'Unknown merge method {download_options.merge_method}')

    # move the file to the output folder
    out_file = os.path.join(tmp_dir, os.path.basename(created_file))
    shutil.move(created_file, out_file)

    if download_options.convert_to_mkv:
      out_file = convert_to_mkv(out_file, delete_original=True)

    # Delete own tmp folder
    shutil.rmtree(my_tmp_dir)

    logger.debug(f'Downloaded MPD to {out_file}')
    return out_file
