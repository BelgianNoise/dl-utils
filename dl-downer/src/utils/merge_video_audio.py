from loguru import logger
import subprocess

from .binaries import get_path_to_binary

def merge_video_audio(
  video_file: str,
  audio_file: str,
  merged_file: str,
):
  command= [
    get_path_to_binary('ffmpeg'),
    '-i', video_file,
    '-i', audio_file,
    '-c:v', 'copy',
    '-c:a', 'copy',
    '-y',
    merged_file,
  ]
  logger.info(f'Merging {video_file} and {audio_file} into {merged_file}')
  subprocess.run(command)
  logger.info(f'Merged successfully!')
