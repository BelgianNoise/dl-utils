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
    merge_method ('period' | 'format'):
      The method to use for merging the files.
      Default is 'period'.
      'period' will merge the files per period.
      'format' will merge the files per format. First all periods' audio files will be merged,
        then all periods' video files will be merged.
        This option is useful when the audio and video of a specific period are not the same length,
        but all segments together are. (Looking at you GoPlay)
    convert_to_mkv (bool):
      Whether to convert the downloaded files to MKV.
      Default is True.
    defragment (bool):
      Whether to defragment the downloaded MP4 files.
      Default is True.
      This is useful for MP4 files that are fragmented, which can cause playback issues in some players.

  '''
  def __init__(
    self,
    video_resolution: str = 'best',
    audio_language: str = 'all',
    subtitle_language: str = 'all',
    decrypt_keys: dict[str, str] = {},
    ignore_periods: List[str] = [],
    merge_method: str = 'period',
    convert_to_mkv: bool = True,
    defragment: bool = True,
  ):
    self.video_resolution = video_resolution
    self.audio_language = audio_language
    self.subtitle_language = subtitle_language
    self.decrypt_keys = decrypt_keys
    self.ignore_periods = ignore_periods
    self.merge_method = merge_method
    self.convert_to_mkv = convert_to_mkv
    self.defragment = defragment
  def __str__(self):
    return f'<MPDDownloadOptions(video_resolution={self.video_resolution}, audio_language={self.audio_language}, subtitle_language={self.subtitle_language})>'
  def __repr__(self):
    return self.__str__()
