import os
import shutil
import time
import uuid
import urllib
import requests
import xml.etree.ElementTree as ET
import concurrent.futures

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

    try:
      init_url = self.initialization
      if not init_url.startswith('http'):
        init_url = urllib.parse.urljoin(base_url, init_url)
      # If init_url contains $RepresentationID$ but representation_id is None, raise an exception
      if '$RepresentationID$' in init_url and representation_id is None:
        raise Exception(f'RepresentationID is required in {init_url} (init) but not provided')
      init_url = init_url.replace('$RepresentationID$', representation_id)

      # Download the init segment
      init_file_type = os.path.splitext(urllib.parse.urlparse(init_url).path)[1].lstrip('.') or 'mp4'
      init_file = os.path.join(my_tmp_dir, f'init.{init_file_type}')
      logger.debug(f'Downloading init segment {init_url}')
      init_response = requests.get(init_url, timeout=20)
      init_response.raise_for_status()
      with open(init_file, 'wb') as f:
        f.write(init_response.content)

      media_url = self.media
      if not media_url.startswith('http'):
        media_url = urllib.parse.urljoin(base_url, media_url)
      # If media_url contains $RepresentationID$ but representation_id is None, raise an exception
      if '$RepresentationID$' in media_url and representation_id is None:
        raise Exception(f'RepresentationID is required in {media_url} (media) but not provided')

      # Download all segments
      logger.info(f'Downloading {len(self.segments)} segments ({self.start_number}-{self.start_number + len(self.segments)}) ...')
      file_type = os.path.splitext(urllib.parse.urlparse(media_url).path)[1].lstrip('.') or 'm4s'

      # use 4 or 75% of CPU threads, whichever is higher
      cpu_count = os.cpu_count() or 4
      max_threads = max(4, int(cpu_count * 0.75))
      logger.debug(f'Using {max_threads} threads to download segments')

      future_to_segment = {}
      with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
        for i, segment in enumerate(self.segments):
          segment_file = os.path.join(my_tmp_dir, f'segment_{str(i).zfill(6)}.{file_type}')

          segment_url = media_url
          segment_url = segment_url.replace('$RepresentationID$', representation_id)
          segment_url = segment_url.replace('$Time$', str(segment.start))
          segment_url = segment_url.replace('$Number$', str(i + self.start_number))

          future = executor.submit(self._download_segment, i, segment_url, segment_file)
          future_to_segment[future] = i

        failed_segments = []
        for future in concurrent.futures.as_completed(future_to_segment):
          try:
            future.result()
          except Exception as error:
            failed_segments.append((future_to_segment[future], error))

      if failed_segments:
        failed_segments = sorted(failed_segments, key=lambda item: item[0])
        first_segment, first_error = failed_segments[0]
        raise Exception(
          f'{len(failed_segments)} segment(s) failed to download. First failed segment index: '
          f'{first_segment}. Error: {first_error}'
        ) from first_error

      # Combine init and segments into one file
      out_file = os.path.join(tmp_dir, f'output-{my_uuid}.mp4')
      with open(out_file, 'wb') as f:
        with open(init_file, 'rb') as init_f:
          f.write(init_f.read())
        missing_files = []
        for i in range(len(self.segments)):
          segment_file = os.path.join(my_tmp_dir, f'segment_{str(i).zfill(6)}.{file_type}')
          if not os.path.exists(segment_file):
            missing_files.append(segment_file)
            continue
          with open(segment_file, 'rb') as segment_f:
            f.write(segment_f.read())

        if missing_files:
          raise FileNotFoundError(
            f'{len(missing_files)} segment file(s) are missing before merge. First missing: {missing_files[0]}'
          )

      logger.info(f'Downloaded segment template {self.initialization} to {out_file} in {time.time() - timer_start:.2f}s')
      return out_file
    finally:
      # Delete own tmp folder even when a download/merge error occurs.
      shutil.rmtree(my_tmp_dir, ignore_errors=True)

  @staticmethod
  def _download_segment(index: int, segment_url: str, segment_file: str):
    retries = 3
    last_error = None
    for attempt in range(1, retries + 1):
      try:
        response = requests.get(segment_url, timeout=20)
        response.raise_for_status()
        if not response.content:
          raise Exception('Empty segment response')
        with open(segment_file, 'wb') as f:
          f.write(response.content)
        return
      except Exception as error:
        last_error = error
        if attempt < retries:
          logger.warning(f'Segment {index} failed on attempt {attempt}/{retries}: {error}. Retrying...')
          time.sleep(0.5 * attempt)
    raise Exception(f'Failed to download segment {index} after {retries} attempts: {segment_url}') from last_error
