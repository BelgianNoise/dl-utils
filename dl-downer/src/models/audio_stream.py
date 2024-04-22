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
