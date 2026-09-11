from src.utils.subtitles import (
  timestamp_to_milliseconds,
  milliseconds_to_timestamp,
  parse_vtt,
  cues_to_srt,
)


class TestTimestampConversion:

  def test_vtt_timestamp_with_hours(self):
    assert timestamp_to_milliseconds('00:00:00.040') == 40

  def test_vtt_timestamp_without_hours(self):
    assert timestamp_to_milliseconds('00:01.500') == 1500

  def test_srt_timestamp(self):
    assert timestamp_to_milliseconds('01:02:03,004') == 3723004

  def test_to_timestamp(self):
    assert milliseconds_to_timestamp(3723004) == '01:02:03,004'

  def test_negative_clamped_to_zero(self):
    assert milliseconds_to_timestamp(-1) == '00:00:00,000'


class TestParseVtt:

  def test_parses_cues_and_strips_tags(self):
    vtt = (
      'WEBVTT\n'
      '\n'
      '00:00:00.040 --> 00:00:03.760 line:90% position:50% align:middle\n'
      '<c.white>Daar ben ik fier op.</c>\n'
      '<c.white>Ik had nog geen werken van Panamarenko.</c>\n'
      '\n'
      '00:00:03.920 --> 00:00:06.400\n'
      '<c.white>Ik vind ze mooi</c>\n'
    )
    cues = parse_vtt(vtt)
    assert cues == [
      (40, 3760, 'Daar ben ik fier op.\nIk had nog geen werken van Panamarenko.'),
      (3920, 6400, 'Ik vind ze mooi'),
    ]

  def test_skips_note_and_style_blocks(self):
    vtt = (
      'WEBVTT\n'
      '\n'
      'NOTE this is a comment\n'
      'still a comment\n'
      '\n'
      'STYLE\n'
      '::cue { color: white; }\n'
      '\n'
      '00:00:01.000 --> 00:00:02.000\n'
      'hello\n'
    )
    cues = parse_vtt(vtt)
    assert cues == [(1000, 2000, 'hello')]


class TestCuesToSrt:

  def test_serializes_cues(self):
    srt = cues_to_srt([(40, 3760, 'Daar ben ik fier op.'), (3920, 6400, 'Ik vind ze mooi')])
    assert srt == (
      '1\n'
      '00:00:00,040 --> 00:00:03,760\n'
      'Daar ben ik fier op.\n'
      '\n'
      '2\n'
      '00:00:03,920 --> 00:00:06,400\n'
      'Ik vind ze mooi\n'
    )
