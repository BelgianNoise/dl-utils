from loguru import logger
from .stream import Stream

class VideoStream(Stream):
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
