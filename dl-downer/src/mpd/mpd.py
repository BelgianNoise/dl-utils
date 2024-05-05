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
from ..utils.files import concat_files

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
    files_to_concat = []

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

      period_file = period.download(my_tmp_dir, self.base_url, download_options)
      files_to_concat.append(period_file)

    if len(files_to_concat) == 0:
      raise Exception(f'No periods were downloaded {self.periods}')
    # some manifests will have multiple periods, in that case we need to concat them
    created_file = files_to_concat[0]
    # concat all files
    if len(files_to_concat) > 1:
      created_file = os.path.join(my_tmp_dir, f'combined-{my_uuid}.mp4')
      concat_files(files_to_concat, created_file)

    # move the file to the output folder
    out_file = os.path.join(tmp_dir, os.path.basename(created_file))
    shutil.move(created_file, out_file)

    # Delete own tmp folder
    shutil.rmtree(my_tmp_dir)

    logger.debug(f'Downloaded MPD to {out_file}')
    return out_file
