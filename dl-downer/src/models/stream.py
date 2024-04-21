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