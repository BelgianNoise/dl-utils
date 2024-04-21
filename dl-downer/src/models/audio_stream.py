from typing import List
import requests
import os
from loguru import logger

from .stream import Stream

class AudioStream(Stream):
  def __init__(
    self,
    lang: str,
    codecs: str,
    channel_count: int,
    media: str,
    initialization: str,
    start_number: int,
    segments: int,
    bandwidth: int,
    id: str,
    audio_sampling_rate: int,
  ):
    self.lang = lang
    self.channel_count = channel_count
    self.codecs = codecs
    self.media = media
    self.initialization = initialization
    self.start_number = start_number
    self.segments = segments
    self.bandwidth = bandwidth
    self.id = id
    self.audio_sampling_rate = audio_sampling_rate

  def __repr__(self) -> str:
    return f'<AudioStream ({self.id}): {self.lang} | {self.channel_count}ch | {self.codecs} | start_number={self.start_number} | segments={self.segments}>'
  def __str__(self) -> str:
    return self.__repr__()

  def copy(self):
    return AudioStream(
      lang=self.lang,
      channel_count=self.channel_count,
      codecs=self.codecs,
      media=self.media,
      initialization=self.initialization,
      start_number=self.start_number,
      segments=self.segments,
      bandwidth=self.bandwidth,
      id=self.id,
      audio_sampling_rate=self.audio_sampling_rate,
    )

  def finalize_init(self, init_filename: str, output_folder: str) -> str:
    filename = f'audio-{self.id}{f".{self.lang}" if self.lang is not None else ""}.mp4'
    output_filename = f'{output_folder}/{filename}'
    os.replace(init_filename, output_filename)
    logger.debug(f'Finalized init.mp4: {init_filename} -> {output_filename}')
    return output_filename

  def get_tmp_dir(self) -> str:
    tmp_dir = f'./tmp/{self.id}'
    os.makedirs(tmp_dir, exist_ok=True)
    logger.debug(f'Created tmp dir: {tmp_dir}')
    return tmp_dir

  def cleanup_tmp_dir(self):
    import shutil
    tmp_dir = f'./tmp/{self.id}'
    shutil.rmtree(tmp_dir)
    logger.debug(f'Removed tmp dir: {tmp_dir}')

  def download(
    self,
    output_folder: str = None,
  ) -> str:
    '''
    Download audio stream

    :return: Path to downloaded audio file
    '''
    logger.debug(f'Downloading audio stream: {self.id} {self.channel_count} {self.codecs} {self.lang}')
    # create tmp dir
    unique_tmp_dir = self.get_tmp_dir()
    # Get the initialization segment
    init_filename = self.download_init(unique_tmp_dir)
    # Get all segments
    self.download_segments(unique_tmp_dir)
    # add content at end of init.mp4
    self.add_segments_to_init(init_filename)
    output_filename = self.finalize_init(init_filename, output_folder)

    logger.debug(f'Audio stream downloaded: {self.id} {self.channel_count} {self.codecs} {self.lang}')

    # remove unique_tmp_dir dir and its content
    self.cleanup_tmp_dir()

    return output_filename
