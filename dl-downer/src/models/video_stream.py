import requests
import os
from loguru import logger

class VideoStream:
  def __init__(
    self,
    width: int,
    height: int,
    frame_rate: int,
    bandwidth: int,
    codecs: str,
    duration: int,
    media: str,
    initialization: str,
    start_number: int,
    segments: int,
    id: str,
    lang: str = None,
  ):
    self.width = width
    self.height = height
    self.frame_rate = frame_rate
    self.bandwidth = bandwidth
    self.codecs = codecs
    self.duration = duration
    self.media = media
    self.initialization = initialization
    self.start_number = start_number
    self.segments = segments
    self.id = id
    self.lang = lang

  def __repr__(self) -> str:
    return f'<VideoStream ({self.id}): {self.width}x{self.height} | {self.frame_rate}fps | {self.bandwidth/1000}kbps | {self.codecs} | {self.duration}s>'
  def __str__(self) -> str:
    return self.__repr__()

  def copy(self):
    return VideoStream(
      width=self.width,
      height=self.height,
      frame_rate=self.frame_rate,
      bandwidth=self.bandwidth,
      codecs=self.codecs,
      duration=self.duration,
      media=self.media,
      initialization=self.initialization,
      start_number=self.start_number,
      segments=self.segments,
      id=self.id,
      lang=self.lang,
    )

  def download(
    self,
    output_folder: str = None,
  ) -> str:
    '''
    Download video stream

    :return: Path to downloaded audio file
    '''
  
    logger.debug(f'Downloading video stream: {self} ')

    unique_tmp_dir = f'./tmp/{self.id}'
    # create tmp dir
    os.makedirs(unique_tmp_dir, exist_ok=True)
    init_filename = f'{unique_tmp_dir}/init.mp4'

    # Get the initialization segment
    init = requests.get(self.initialization)
    with open(init_filename, 'wb') as f:
      f.write(init.content)

    # Get all segments
    saved_segments = []
    last_segment = self.start_number + self.segments + 1
    for i in range(self.start_number, last_segment):
      segment = requests.get(self.media.replace('$Number$', str(i)))
      with open(f'{unique_tmp_dir}/segment_{i}.m4s', 'wb') as f:
        f.write(segment.content)
      saved_segments.append(f'{unique_tmp_dir}/segment_{i}.m4s')

    # add content at end of init.mp4
    with open(init_filename, 'ab') as f_init:
      for segment in saved_segments:
        with open(segment, 'rb') as f_segment:
          f_init.write(f_segment.read())

    # rename init.mp4 to audio.mp4
    filename = f'video-{self.id}{f".{self.lang}" if self.lang is not None else ""}.mp4'
    if output_folder is None:
      output_filename = f'./tmp/{filename}'
    else:
      output_filename = f'{output_folder}/{filename}'
    os.replace(init_filename, output_filename)

    logger.debug(f'Video stream downloaded: {self}')

    # remove unique_tmp_dir dir and its content
    import shutil
    shutil.rmtree(unique_tmp_dir)

    return output_filename
