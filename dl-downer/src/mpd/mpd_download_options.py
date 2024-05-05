from typing import List

class MPDDownloadOptions():
  '''
  MPDDownloadOptions is a class that represents the options for downloading an MPD manifest.

  Attributes:
    video_resolution (str):
      The video resolution to download.
      Default is 'best'.
      This can be either the specifc width, specific height, or a specific resolution.
      Examples: '1920x1080', '720', '1080', ...
    audio_language (str):
      The audio language to download. Default is 'all'.
      Advised to leave this at the default value.
      Audio streams that do not list a language will NOT be included when not set to 'all'.
      Examples: 'en', 'nl', 'nld', ...
    subtitle_language (str):
      The subtitle language to download. Default is 'all'.
      Advised to leave this at the default value.
      Subtitles that do not list a language will NOT be included when not set to 'all'.
      Examples: 'en', 'nl', 'nld', ...
    decrypt_keys (dict[str, str]):
      A dictionary containing the keys to decrypt the files.
      The keys are in the format: {key_id: key_value}.
      Example: {'08': '1234567890ABCDEF1234567890ABCDEF'}
    ignore_periods (List[str]):
      A list of periods to ignored, as a regex pattern.
      Example: [ '^pre-roll.*' ]
  '''
  def __init__(
    self,
    video_resolution: str = 'best',
    audio_language: str = 'all',
    subtitle_language: str = 'all',
    decrypt_keys: dict[str, str] = {},
    ignore_periods: List[str] = [],
  ):
    self.video_resolution = video_resolution
    self.audio_language = audio_language
    self.subtitle_language = subtitle_language
    self.decrypt_keys = decrypt_keys
    self.ignore_periods = ignore_periods
  def __str__(self):
    return f'<MPDDownloadOptions(video_resolution={self.video_resolution}, audio_language={self.audio_language}, subtitle_language={self.subtitle_language})>'
  def __repr__(self):
    return self.__str__()
