class DownloadResult:
  '''Standardized result returned by every platform downloader.'''

  def __init__(
    self,
    file_path: str,
    title: str,
    platform: str,
    extension: str,
    suggested_filepath: str,
    season: str = None,
    episode: str = None,
  ):
    self.file_path = file_path
    self.title = title
    self.platform = platform
    self.extension = extension
    self.suggested_filepath = suggested_filepath
    self.season = season
    self.episode = episode
