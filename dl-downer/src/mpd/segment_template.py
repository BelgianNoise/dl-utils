import os
import shutil
import time
import uuid
import urllib
import requests
import xml.etree.ElementTree as ET

from typing import List
from loguru import logger

from .segment import Segment

class SegmentTemplate:
  def __init__(
    self,
    initialization: str,
    media: str,
    timescale: int = None,
    start_number: int = 0,
    presentation_time_offset: int = None,
  ):
    self.initialization = initialization
    self.media = media
    self.timescale = timescale
    self.start_number = start_number
    self.presentation_time_offset = presentation_time_offset
    self.segments: List[Segment] = []
  
  def __str__(self):
    return f'<SegmentTemplate(initialization={self.initialization}, media={self.media}, timescale={self.timescale}, start_number={self.start_number}, presentation_time_offset={self.presentation_time_offset}, segments={len(self.segments)})>'
  def __repr__(self):
    return self.__str__()
  
  @staticmethod
  def from_element(element: ET.Element):
    logger.debug(f'Parsing SegmentTemplate with initialization: {element.get("initialization")}')
    timescale = element.get('timescale')
    start_number = element.get('startNumber')
    presentation_time_offset = element.get('presentationTimeOffset')
    segment_template = SegmentTemplate(
      initialization=element.get('initialization'),
      media=element.get('media'),
      timescale=int(timescale) if timescale is not None else None,
      start_number=int(start_number) if start_number is not None else 0,
      presentation_time_offset=int(presentation_time_offset) if presentation_time_offset is not None else None,
    )

    segments = element.findall('SegmentTimeline/S')
    if len(segments) > 0:
      current_t = 0 # default to 0
      if segments[0].get('t') is not None:
        current_t = int(segments[0].get('t'))
      # sometimes the first segment does not have a start time
      elif segment_template.start_number is not None:
        current_t = segment_template.start_number
      
      for segment in segments:
        dur = int(segment.get('d'))
        seg_t = None
        if segment.get('t') is not None:
          seg_t = int(segment.get('t'))
          # both should technically be the same
          if seg_t != current_t:
            logger.warning(f'Base time {seg_t} does not match current time {current_t}')
          current_t = seg_t
        segment_template.segments.append(Segment(
          start=seg_t if seg_t is not None else current_t,
          duration=dur
        ))
        current_t += dur
        # if repeat is present, repeat the segment
        if segment.get('r') is not None:
          for _ in range(int(segment.get('r'))):
            segment_template.segments.append(Segment(
              start=current_t,
              duration=dur
            ))
            current_t += dur

    return segment_template

  def download(
    self,
    tmp_dir: str,
    base_url: str,
    representation_id: str,
  ) -> str:
    ''':return: the path to the downloaded segment template mp4 file'''
    logger.debug(f'Downloading segment template {self.initialization}')

    timer_start = time.time()

    # Create a temporary folder
    my_uuid = str(uuid.uuid4())[:8]
    my_tmp_dir = os.path.join(tmp_dir, f'segment-template-{my_uuid}')
    os.makedirs(my_tmp_dir, exist_ok=True)

    init_url = self.initialization
    if not init_url.startswith('http'):
      init_url = urllib.parse.urljoin(base_url, init_url)
    # If init_url contains $RepresentationID$ but representation_id is None, raise an exception
    if '$RepresentationID$' in init_url and representation_id is None:
      raise Exception(f'RepresentationID is required in {init_url} (init) but not provided')
    init_url = init_url.replace('$RepresentationID$', representation_id)

    # Download the init segment
    init_file_type = init_url.split('.')[-1]
    init_file = os.path.join(my_tmp_dir, f'init.{init_file_type}')
    with open(init_file, 'wb') as f:
      logger.debug(f'Downloading init segment {init_url}')
      f.write(requests.get(init_url).content)
    
    media_url = self.media
    if not media_url.startswith('http'):
      media_url = urllib.parse.urljoin(base_url, media_url)
    # If media_url contains $RepresentationID$ but representation_id is None, raise an exception
    if '$RepresentationID$' in media_url and representation_id is None:
      raise Exception(f'RepresentationID is required in {media_url} (media) but not provided')

    # Download all segments
    logger.info(f'Downloading {len(self.segments)} segments ({self.start_number}-{self.start_number + len(self.segments)}) ...')
    file_type = media_url.split('.')[-1]

    import concurrent.futures

    def download_segment(segment_url, segment_file):
      response = requests.get(segment_url)
      with open(segment_file, 'wb') as f:
        f.write(response.content)
    # use 4 or 75% of CPU threads, whichever is higher
    max_threads = max(4, int(os.cpu_count() * 0.75))
    logger.debug(f'Using {max_threads} threads to download segments')
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
      futures = []
      for i, segment in enumerate(self.segments):
        segment = self.segments[i]
        segment_file = os.path.join(my_tmp_dir, f'segment_{str(i).zfill(6)}.{file_type}')

        segment_url = media_url
        segment_url = segment_url.replace('$RepresentationID$', representation_id)
        segment_url = segment_url.replace('$Time$', str(segment.start))
        segment_url = segment_url.replace('$Number$', str(i + self.start_number))

        futures.append(executor.submit(download_segment, segment_url, segment_file))

      # Wait for all the futures to complete
      concurrent.futures.wait(futures)
    
    # Combine init and segments into one file
    out_file = os.path.join(tmp_dir, f'output-{my_uuid}.mp4')
    with open(out_file, 'wb') as f:
      f.write(open(init_file, 'rb').read())
      for i in range(len(self.segments)):
        segment_file = os.path.join(my_tmp_dir, f'segment_{str(i).zfill(6)}.{file_type}')
        f.write(open(segment_file, 'rb').read())

    #Delete own tmp folder
    shutil.rmtree(my_tmp_dir)

    logger.info(f'Downloaded segment template {self.initialization} to {out_file} in {time.time() - timer_start:.2f}s')
    return out_file