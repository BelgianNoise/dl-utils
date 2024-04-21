
from typing import List
from xml.etree import ElementTree as ET

from ..models.video_stream import VideoStream
from ..models.audio_stream import AudioStream

def get_all_audio_streams(
  root: ET.Element,
) -> List[AudioStream]:
  '''
  Get all audio streams from the MPD root

  :param root: Root of the MPD XML
  :return: List of Tuples containing audio sampling rate, codecs, id, and bandwidth
  '''
  audio_streams = []
  for period in root.findall('Period'):
    for adaptation_set in period.findall('AdaptationSet[@mimeType="audio/mp4"]'):
      channels = adaptation_set.find('AudioChannelConfiguration')
      channels = channels.attrib['value']
      lang = adaptation_set.attrib['lang']
      for representation in adaptation_set.findall('Representation'):
        segment_template = representation.find('SegmentTemplate')
        segment_timeline = segment_template.find('SegmentTimeline')
        segments = 0
        for s in segment_timeline.findall('S'):
          if 'r' in s.attrib:
            segments += int(s.attrib['r'])
          else:
            segments += 1
        audio_streams.append(AudioStream(
          lang,
          representation.attrib['codecs'],
          int(channels),
          segment_template.attrib['media'],
          segment_template.attrib['initialization'],
          int(segment_template.attrib['startNumber']),
          segments,
          int(representation.attrib['bandwidth']),
          representation.attrib['id'],
          int(representation.attrib['audioSamplingRate']),
        ))

  return audio_streams

def get_all_video_streams(
  root: ET.Element,
) -> List[VideoStream]:
  '''
  Get all video streams from the MPD root

  :param root: Root of the MPD XML
  :return: List of video streams
  '''

  video_streams = []
  for period in root.findall('Period'):
    for adaptation_set in period.findall('AdaptationSet[@mimeType="video/mp4"]'):
      for representation in adaptation_set.findall('Representation'):
        segment_template = representation.find('SegmentTemplate')
        segment_timeline = segment_template.find('SegmentTimeline')
        segments = 0
        for s in segment_timeline.findall('S'):
          if 'r' in s.attrib:
            segments += int(s.attrib['r'])
          else:
            segments += 1
        period_duration = period.attrib['duration']
        # transform "PT16M14.6S" into seconds
        duration = int(period_duration.split('M')[0].split('PT')[1]) * 60
        duration += int(period_duration.split('M')[1].split('.')[0])
        video_streams.append(VideoStream(
          width=int(representation.attrib['width']),
          height=int(representation.attrib['height']),
          frame_rate=int(representation.attrib['frameRate']),
          bandwidth=int(representation.attrib['bandwidth']),
          codecs=representation.attrib['codecs'],
          duration=duration,
          media=segment_template.attrib['media'],
          initialization=segment_template.attrib['initialization'],
          start_number=int(segment_template.attrib['startNumber']),
          segments=segments,
          id=representation.attrib['id'],
        ))

  return video_streams
