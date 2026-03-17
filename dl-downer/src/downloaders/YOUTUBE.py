import os
import subprocess

from loguru import logger

from ..models.dl_request import DLRequest
from ..models.download_result import DownloadResult
from ..models.dl_request_platform import DLRequestPlatform

def YOUTUBE_DL(dl_request: DLRequest):
  
  command = [ 'yt-dlp',
    '--yes-playlist',
    '-N', '4',
    '--restrict-filenames',
    '--write-subs',
    '--sub-langs', 'all',
    '--merge-output-format', 'mkv',
  ]

  if dl_request.preferred_quality_matcher:
    p = dl_request.preferred_quality_matcher
    if p != 'best':
      command.extend([ '-f', f'bv[height<={p}]+ba/b[height<={p}]' ])

  filename = '%(title)s.%(ext)s'
  if dl_request.output_filename:
    filename = f'{dl_request.output_filename}.%(ext)s'
  file_path = os.path.join(
    os.getenv('DOWNLOADS_FOLDER', './downloads'),
    dl_request.platform,
    filename,
  )

  command.extend([ '-o', file_path ])
  command.extend([ dl_request.video_page_or_manifest_url ])

  # Use --print to capture the actual output filepath after merging
  command.extend(['--print', 'after_move:filepath'])

  logger.debug(f'Running command: {command}')
  proc = subprocess.run(command, capture_output=True, text=True)
  logger.debug(f'yt-dlp stdout: {proc.stdout}')
  if proc.stderr:
    logger.debug(f'yt-dlp stderr: {proc.stderr}')

  # The last non-empty line of stdout is the resolved filepath
  resolved_path = proc.stdout.strip().splitlines()[-1].strip() if proc.stdout.strip() else file_path
  title = os.path.splitext(os.path.basename(resolved_path))[0]

  return DownloadResult(
    file_path=resolved_path,
    title=title,
    platform=DLRequestPlatform.YOUTUBE.value,
    extension='mkv',
    suggested_filepath=resolved_path,
  )