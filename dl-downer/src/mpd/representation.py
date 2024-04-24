import os
import shutil
import uuid
import xml.etree.ElementTree as ET

from loguru import logger

from .segment_template import SegmentTemplate

class Representation:
  def __init__(
    self,
    id: str,
    width: int = None,
    height: int = None,
    frame_rate: int = None,
    bandwidth: int = None,
    codecs: str = None,
    scan_type: str = None,
    segment_template: SegmentTemplate = None,
    audio_sampling_rate: int = None,
  ):
    self.id = id
    self.bandwidth = bandwidth
    self.width = width
    self.height = height
    self.frame_rate = frame_rate
    self.codecs = codecs
    self.scan_type = scan_type
    self.segment_template = segment_template
    self.audio_sampling_rate = audio_sampling_rate
  def __str__(self):
    return f'<Representation(id={self.id}, width={self.width}, height={self.height}, frame_rate={self.frame_rate}, bandwidth={self.bandwidth}, codecs={self.codecs})>'
  def __repr__(self):
    return self.__str__()
  @staticmethod
  def from_element(el: ET.Element) -> 'Representation':
    logger.debug(f'Parsing Representation with id: {el.get("id")}')
    segment_template = None
    seg_temp_el = el.find('SegmentTemplate')
    if seg_temp_el is not None:
      segment_template = SegmentTemplate.from_element(seg_temp_el)
    
    return Representation(
      id=el.get('id'),
      width=int(el.get('width')) if el.get('width') is not None else None,
      height=int(el.get('height')) if el.get('height') is not None else None,
      frame_rate=int(el.get('frameRate').split('/')[0]) if el.get('frameRate') is not None else None,
      bandwidth=int(el.get('bandwidth')) if el.get('bandwidth') is not None else None,
      codecs=el.get('codecs'),
      scan_type=el.get('scanType'),
      segment_template=segment_template,
      audio_sampling_rate=int(el.get('audioSamplingRate')) if el.get('audioSamplingRate') is not None else None,
    )
  
  def download(
    self,
    tmp_dir: str,
    base_url: str,
    segment_template: SegmentTemplate = None,
  ) -> str:
    ''':return: the path to the downloaded representation mp4 file'''
    logger.debug(f'Downloading {self}')

    use_template = self.segment_template
    if use_template is None:
      use_template = segment_template
      if use_template is None:
        raise Exception('No segment template found')

    # Create a temporary folder
    my_tmp_dir = os.path.join(tmp_dir, f'representation-{str(uuid.uuid4())[:8]}')
    os.makedirs(my_tmp_dir, exist_ok=True)
    created_file = use_template.download(my_tmp_dir, base_url, self.id)

    # Move the file to the parent folder
    out_file = os.path.join(tmp_dir, os.path.basename(created_file))
    shutil.move(created_file, out_file)

    # Delete own tmp folder
    shutil.rmtree(my_tmp_dir)

    logger.debug(f'Downloaded {self} to {out_file}')
    return out_file
