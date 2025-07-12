import os
import re
import shutil
import uuid
import xml.etree.ElementTree as ET

from typing import List
from loguru import logger

from .segment_template import SegmentTemplate
from .representation import Representation
from .mpd_download_options import MPDDownloadOptions
from ..utils.files import decrypt_file, defragment_mp4

class AdaptationSet:
  def __init__(
    self,
    id: str,
    mime_type: str,
    segment_alignment: bool = None,
    start_with_sap: int = None,
    subsegment_alignment: bool = None,
    subsegment_starts_with_sap: int = None,
    bitstream_switching: bool = None,
    group: str = None,
    content_type: str = None,
    par: str = None,
    min_bandwidth: int = None,
    max_bandwidth: int = None,
    max_width: int = None,
    max_height: int = None,
    min_frame_rate: int = None,
    max_frame_rate: int = None,
    sar: str = None,
    lang: str = None,
    segment_template = None,
    representations: List[Representation] = [],
    has_content_protections: bool = False,
  ):
    self.id = id
    self.mime_type = mime_type
    self.segment_alignment = segment_alignment
    self.start_with_sap = start_with_sap
    self.subsegment_alignment = subsegment_alignment
    self.subsegment_starts_with_sap = subsegment_starts_with_sap
    self.bitstream_switching = bitstream_switching
    self.group = group
    self.content_type = content_type
    self.par = par
    self.min_bandwidth = min_bandwidth
    self.max_bandwidth = max_bandwidth
    self.max_width = max_width
    self.max_height = max_height
    self.min_frame_rate = min_frame_rate
    self.max_frame_rate = max_frame_rate
    self.sar = sar
    self.lang = lang
    self.segment_template = segment_template
    self.representations = representations
    self.has_content_protections = has_content_protections
  def __str__(self):
    return f'<AdaptationSet(id={self.id}, mime_type={self.mime_type}, content_type={self.content_type})>'
  def __repr__(self):
    return self.__str__()
  @staticmethod
  def from_element(el: ET.Element)  -> 'AdaptationSet':
    logger.debug(f'Parsing AdaptationSet with id: {el.get("id")}')
    segment_template = None
    seg_temp_el = el.find('./SegmentTemplate')
    if seg_temp_el is not None:
      segment_template = SegmentTemplate.from_element(seg_temp_el)

    representations = []
    for representation in el.findall('./Representation'):
      representations.append(Representation.from_element(representation))

    has_content_protections = True if el.find('./ContentProtection') is not None else False

    return AdaptationSet(
      id=el.get('id'),
      mime_type=el.get('mimeType'),
      segment_alignment=el.get('segmentAlignment') == 'true',
      start_with_sap=int(el.get('startWithSAP')) if el.get('startWithSAP') is not None else None,
      subsegment_alignment=el.get('subsegmentAlignment') == 'true',
      subsegment_starts_with_sap=int(el.get('subsegmentStartsWithSAP')) if el.get('subsegmentStartsWithSAP') is not None else None,
      bitstream_switching=el.get('bitstreamSwitching') == 'true',
      group=el.get('group'),
      content_type=el.get('contentType'),
      par=el.get('par'),
      min_bandwidth=int(el.get('minBandwidth')) if el.get('minBandwidth') is not None else None,
      max_bandwidth=int(el.get('maxBandwidth')) if el.get('maxBandwidth') is not None else None,
      max_width=int(el.get('maxWidth')) if el.get('maxWidth') is not None else None,
      max_height=int(el.get('maxHeight')) if el.get('maxHeight') is not None else None,
      min_frame_rate=int(el.get('minFrameRate')) if el.get('minFrameRate') is not None else None,
      max_frame_rate=int(el.get('maxFrameRate')) if el.get('maxFrameRate') is not None else None,
      sar=el.get('sar'),
      lang=el.get('lang'),
      segment_template=segment_template,
      representations=representations,
      has_content_protections=has_content_protections,
    )

  def download(
    self,
    tmp_dir: str,
    base_url: str,
    download_options: MPDDownloadOptions = None,
  ) -> str:
    '''
    Downloads the adaptation set to the tmp_dir.

    :return: the path to the downloaded adaptation set mp4 file
    '''
    logger.debug(f'Downloading adaptation set {self.id}')
    # Create a temporary folder
    my_tmp_dir = os.path.join(tmp_dir, f'adaptation-set-{str(uuid.uuid4())[:8]}')
    os.makedirs(my_tmp_dir, exist_ok=True)
    # download the first representation
    if len(self.representations) == 0:
      raise Exception('No representations found')
    
    # download the first representation
    representation_to_download = self.representations[0]
    # check download options
    if download_options is not None:
      # 1 AdaptationSet usually respresents one language
      # so I assume we only have one representation per language
      # not taking into account bandwidth/bitrate
      if self.mime_type.startswith('audio/'):
        if download_options.audio_language is not None:
          if download_options.audio_language != 'all':
            if self.lang != download_options.audio_language:
              logger.debug(f'Skipping {self.lang} audio track')
              representation_to_download = None
      # Video AdaptationSet usually has multiple representations
      # choose the best one based on the video_resolution
      elif self.mime_type.startswith('video/'):
        if download_options.video_resolution is not None:
          if download_options.video_resolution == 'best':
            # if 'best' is selected we are guaranted to end up
            # with a representation.
            # loop over all and find highest vidoe width
            for representation in self.representations:
              if representation.width is None:
                continue
              if representation_to_download.width is None or representation.width > representation_to_download.width:
                representation_to_download = representation
          else:
            # reset representation_to_download
            # we are not guaranteed to find a representation
            # that matches the video_resolution
            representation_to_download = None
            # loop over all and find matching video by checking if
            # video_resolution is in f'{width}x{height}'
            for representation in self.representations:
              if representation.width is None or representation.height is None:
                continue
              if download_options.video_resolution in f'{representation.width}x{representation.height}':
                representation_to_download = representation
                break
      else:
        # Add more cases later here for subtitles etc.
        # will return None for now
        pass

    # no appropriate representation found
    if representation_to_download is None:
      return None

    logger.debug(f'Selected representation: {self.mime_type} | {representation_to_download.codecs} | {representation_to_download.width}x{representation_to_download.height} | {representation_to_download.bandwidth}bps')
    created_file = representation_to_download.download(my_tmp_dir, base_url, self.segment_template)
    
    if self.has_content_protections:
      if download_options is None or len(download_options.decrypt_keys) == 0:
        raise Exception('Content is encrypted, but no decryption keys provided')

    if download_options is not None:
      if len(download_options.decrypt_keys) > 0:
        # decrypt the file
        decrypted_file = decrypt_file(created_file, download_options.decrypt_keys)
        # replace created_file with decrypted_file
        created_file = decrypted_file

    if download_options.defragment:
      # defragment the file, just in case
      defragmented_file = os.path.join(my_tmp_dir, f'defrag-{os.path.basename(created_file)}')
      defragment_mp4(created_file, defragmented_file)
      created_file = defragmented_file

    # Move the file to the parent folder
    mime_type_escaped = re.sub(r'[^a-zA-Z0-9]', '-', self.mime_type)
    out_file = os.path.join(tmp_dir, f'{mime_type_escaped}-{os.path.basename(created_file)}')
    shutil.move(created_file, out_file)

    # Delete own tmp folder
    shutil.rmtree(my_tmp_dir)

    logger.debug(f'Downloaded adaptation set {self.id} to {out_file}')
    return out_file
