import requests
import os
from typing import List
from loguru import logger

class Stream():
  '''
  Generic Stream class not to be used directly
  '''

  def download_segments(self, tmp_dir: str) -> List[str]:
    '''
    Download all segments of the stream to the tmp_dir

    :param tmp_dir: Temporary directory to save the segments
    :returns: List of paths to the downloaded segments
    '''

    logger.debug(f'Downloading {self.segments} {self.__class__.__name__} segments: {self.id}')
    saved_segments = []
    last_segment = self.start_number + self.segments
    for i in range(self.start_number, last_segment + 1):
      segment = requests.get(self.media.replace('$Number$', str(i)))
      if segment.status_code != 200:
        logger.error(f'Error downloading segment {i}: {segment.status_code}')
      with open(f'{tmp_dir}/segment_{i}.m4s', 'wb') as f:
        f.write(segment.content)
      saved_segments.append(f'{tmp_dir}/segment_{i}.m4s')
    logger.debug(f'Downloaded {self.segments} {self.__class__.__name__} segments: {self.id}')
    return saved_segments

  def download_init(self, tmp_dir: str) -> str:
    '''
    Download the initialization segment of the stream to the tmp_dir

    :param tmp_dir: Temporary directory to save the initialization segment
    :returns: Path to the downloaded initialization segment
    '''

    logger.debug(f'Downloading {self.__class__.__name__} initialization segment: {self.id}')
    init_filename = f'{tmp_dir}/init.mp4'
    init = requests.get(self.initialization)
    with open(init_filename, 'wb') as f:
      f.write(init.content)
    logger.debug(f'Downloaded {self.__class__.__name__} initialization segment: {self.id}')
    return init_filename

  def add_segments_to_init(self, init_filename: str) -> None:
    '''
    Looks for all segments in the same directory as the
    init_filename and appends them to the init_filename

    :param init_filename: Path to the init.mp4 file
    :returns: None
    '''

    logger.debug(f'Adding segments to init.mp4: {init_filename}')
    init_folder = os.path.dirname(init_filename)
    # find all segments in init_folder
    segments = [f for f in os.listdir(init_folder) if os.path.isfile(os.path.join(init_folder, f)) and f.startswith('segment_')]
    # sort segments
    segments.sort(key=lambda x: int(x.split('_')[1].split('.')[0].zfill(6)))
    logger.debug(f'Found {len(segments)} segments to add to init.mp4: {init_filename}')
    # append all segments to init.mp4
    with open(init_filename, 'ab') as init_file:
      for segment in segments:
        with open(f'{init_folder}/{segment}', 'rb') as segment_file:
          init_file.write(segment_file.read())
    logger.debug(f'Added {len(segments)} segments to init.mp4: {init_filename}')
  
  def get_tmp_dir(self) -> str:
    tmp_dir = f'./tmp/{self.id}'
    os.makedirs(tmp_dir, exist_ok=True)
    logger.debug(f'Created tmp dir: {tmp_dir}')
    return tmp_dir

  def cleanup_tmp_dir(self):
    import shutil
    tmp_dir = f'./tmp/{self.id}'
    shutil.rmtree(tmp_dir)
    logger.debug(f'Removed tmp dir: {tmp_dir}')
  
  def finalize_init(self, init_filename: str, output_folder: str) -> str:
    if "video" in self.__class__.__name__.lower():
      filename = f'video-{self.id}{f".{self.lang}" if self.lang is not None else ""}.mp4'
    elif "audio" in self.__class__.__name__.lower():
      filename = f'audio-{self.id}{f".{self.lang}" if self.lang is not None else ""}.mp4'
    else:
      filename = f'{self.id}.mp4'
    output_filename = f'{output_folder}/{filename}'
    os.replace(init_filename, output_filename)
    logger.debug(f'Finalized init.mp4: {init_filename} -> {output_filename}')
    return output_filename

  def download(
    self,
    output_folder: str = None,
  ) -> str:
    '''
    Download stream

    :return: Path to downloaded file
    '''
    logger.debug(f'Downloading {self.__class__.__name__} stream: {self}')
    # create tmp dir
    unique_tmp_dir = self.get_tmp_dir()
    # Get the initialization segment
    init_filename = self.download_init(unique_tmp_dir)
    # Get all segments
    self.download_segments(unique_tmp_dir)
    # add content at end of init.mp4
    self.add_segments_to_init(init_filename)
    output_filename = self.finalize_init(init_filename, output_folder)

    logger.debug(f'{self.__class__.__name__} downloaded: {self}')

    # remove unique_tmp_dir dir and its content
    self.cleanup_tmp_dir()

    return output_filename