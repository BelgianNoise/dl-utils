import os
import shutil
import subprocess
from typing import List
import uuid
from loguru import logger

def decrypt_file(
  filename: str,
  keys: dict[str, str],
) -> str:
  '''Decrypts the file using the keys provided using mp4decrypt'''

  logger.debug(f'Decrypting {filename} using {keys}')
  decrypted_filename = os.path.join(
    os.path.dirname(filename),
    f'decrypted-{os.path.basename(filename)}',
  )

  command = [ 'mp4decrypt', '--show-progress' ]
  for k, v in keys.items():
    command.extend([ '--key', f'{k}:{v}'])
  command.extend([ filename, decrypted_filename ])

  logger.debug(f'Running command: {" ".join(command)}')
  subprocess.run(command, check=True)

  logger.debug(f'Decrypted file into {decrypted_filename}')
  return decrypted_filename

def concat_files(
  files: List[str],
  out_file: str,
) -> str:
  '''Concatenates all files into one file using ffmpeg'''

  logger.debug(f'Concatenating files {files} into {out_file}')
  
  # Create a temporary folder
  my_uuid = str(uuid.uuid4())[:8]
  my_tmp_dir = os.path.join(os.path.dirname(files[0]), f'/concat-{my_uuid}')
  os.makedirs(my_tmp_dir, exist_ok=True)

  # copy all files to temporary folder
  for f in files:
    shutil.copy(f, my_tmp_dir)

  # add all files to concat list txt
  concat_list_file = f'{my_tmp_dir}/concat_list.txt'
  with open(concat_list_file, 'w') as f_write:
    for f in files:
      f_write.write(f"file '{os.path.basename(f)}'\n")

  command = [ 'ffmpeg',
    '-f', 'concat',
    '-i', concat_list_file,
    '-safe', '0',
    '-c:a', 'copy',
    '-c:v', 'copy',
    '-y',
    '-loglevel', 'warning',
    out_file
  ]

  logger.debug(f'Running command: {" ".join(command)}')
  subprocess.run(command, check=True)

  # Delete own tmp folder
  shutil.rmtree(my_tmp_dir)

  logger.debug(f'Concatenated files into {out_file}')
  return out_file

def merge_files(
  input_files: List[str],
  output_file: str,
):
  command = [ 'ffmpeg' ]
  
  for input_file in input_files:
    command.extend([
      '-i', input_file,
    ])

  command.extend([
    '-c:v', 'copy',
    '-c:a', 'copy',
    '-y',
    output_file,
  ])

  logger.info(f'Merging {input_files} into {output_file}...')
  subprocess.run(command, check=True)
  logger.info(f'Merged successfully!')

def insert_subtitle(
  input_file: str,
  subtitle_file: str,
):
  did_convert = False
  # convert to srt if subtitle if needed
  if subtitle_file.endswith('.vtt'):
    converted_subtitle_file = os.path.join(
      os.path.dirname(subtitle_file),
      f'{os.path.basename(subtitle_file)[:-4]}.srt',
    )
    command = [ 'ffmpeg',
      '-i', subtitle_file,
      converted_subtitle_file,
    ]
    logger.info(f'Converting {subtitle_file} to srt...')
    subprocess.run(command, check=True)
    subtitle_file = converted_subtitle_file
    did_convert = True
    logger.info(f'Converted successfully!')

  temp_output_file = os.path.join(
    os.path.dirname(input_file),
    f'subbed_{os.path.basename(input_file)}',
  )
  command = [ 'ffmpeg',
    '-i', input_file,
    '-i', subtitle_file,
    '-c', 'copy',
    '-y',
    temp_output_file,
  ]

  logger.info(f'Inserting subtitle {subtitle_file} into {input_file}...')
  subprocess.run(command, check=True)
  # Move the temp file to the original file + overwrite
  shutil.move(temp_output_file, input_file)
  # if subs were converted, remove the converted file
  if did_convert:
    os.remove(subtitle_file)
  logger.info(f'Subtitle inserted successfully!')

def convert_to_mkv(
  input_file: str,
  delete_original: bool = False,
):
  output_file = os.path.join(
    os.path.dirname(input_file),
    f'{os.path.basename(input_file)[:-4]}.mkv',
  )
  command = [ 'ffmpeg',
    '-i', input_file,
    '-c', 'copy',
    '-y',
    output_file,
  ]

  logger.info(f'Converting {input_file} to mkv...')
  subprocess.run(command, check=True)
  logger.info(f'Converted successfully!')

  if delete_original:
    logger.debug(f'Deleting original file {input_file}')
    os.remove(input_file)

  return output_file
