import os
import subprocess
import uuid

from typing import List
from loguru import logger

from .binaries import get_path_to_binary

def concat_files(
  files: List[str],
  output_file: str,
) -> str:
  '''
  Concatanate files using ffmpeg.
  All files should be in the same folder.

  :return: Path to concatanated file
  '''

  logger.debug(f'Concatanating files: {files}')

  folder = os.path.dirname(files[0])
  uuid_value = str(uuid.uuid4())
  txt_file = f'{folder}/{uuid_value}.txt'
  with open(txt_file, 'a') as f_txt:
    for f in files:
      # add the filename to the txt file
      f_txt.write(f'file \'{os.path.basename(f)}\'\n')
  
  command = [
    get_path_to_binary('ffmpeg'),
    '-f', 'concat',
    '-safe', '0',
    '-i', txt_file,
    '-c', 'copy',
    '-y', # auto overwrite output file
    output_file,
  ]
  logger.debug(f'Calling ffmpeg ... {command}')
  subprocess.run(command)

  os.remove(txt_file)

  logger.info(f'Finished concatanating files to {output_file}')
  
  return output_file
