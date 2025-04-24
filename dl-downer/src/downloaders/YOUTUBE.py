import os
import subprocess

from loguru import logger

from ..models.dl_request import DLRequest

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

  logger.debug(f'Running command: {command}')
  subprocess.run(command)
