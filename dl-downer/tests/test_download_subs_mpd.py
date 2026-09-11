from types import SimpleNamespace
from unittest.mock import patch

from src.utils.download_subs_mpd import download_subs_mpd


def _rep(base_url):
  return SimpleNamespace(base_url=base_url)


def _adaptation(lang='nl', mime_type='text/vtt', reps=None):
  return SimpleNamespace(
    id='as',
    mime_type=mime_type,
    lang=lang,
    representations=reps if reps is not None else [],
  )


def _period(pid, duration, adaptation_sets):
  return SimpleNamespace(id=pid, duration=duration, adaptation_sets=adaptation_sets)


def _mpd(periods):
  return SimpleNamespace(base_url='https://example.com/', periods=periods)


def _vtt(first_cue_start='00:00:00.000'):
  return (
    'WEBVTT\n'
    '\n'
    f'{first_cue_start} --> 00:00:01.000\n'
    'hello\n'
  )


class TestDownloadSubsMpd:

  def test_shifts_cues_by_exact_period_durations(self, tmp_path, monkeypatch):
    monkeypatch.setenv('DOWNLOADS_FOLDER', str(tmp_path))

    # content 1 (16m35.48s), a 3s mid-roll, then content 2
    mpd = _mpd([
      _period('p0', 995480, [_adaptation(lang='nl', reps=[_rep('subs/P0.vtt')])]),
      _period('mid-roll-1-ad-1', 3000, []),
      _period('p1', 1110440, [_adaptation(lang='nl', reps=[_rep('subs/P1.vtt')])]),
    ])

    def fake_get(url):
      if url.endswith('P0.vtt'):
        return SimpleNamespace(text=_vtt('00:00:00.000'), raise_for_status=lambda: None)
      if url.endswith('P1.vtt'):
        return SimpleNamespace(text=_vtt('00:00:00.000'), raise_for_status=lambda: None)
      raise AssertionError(f'unexpected url {url}')

    with patch('src.utils.download_subs_mpd.requests.get', side_effect=fake_get):
      files = download_subs_mpd(
        mpd=mpd,
        filename='Episode',
        platform=SimpleNamespace(value='GOPLAY'),
        ignore_periods=['^mid-roll.*'],
      )

    assert len(files) == 1
    content = open(files[0], encoding='utf-8').read()
    # first cue stays at 0s, second cue is shifted by the exact 995.48s duration
    assert '00:00:00,000 --> 00:00:01,000' in content
    assert '00:16:35,480 --> 00:16:36,480' in content

  def test_ignored_period_does_not_contribute_offset(self, tmp_path, monkeypatch):
    monkeypatch.setenv('DOWNLOADS_FOLDER', str(tmp_path))

    mpd = _mpd([
      _period('p0', 1000, [_adaptation(lang='nl', reps=[_rep('subs/P0.vtt')])]),
      _period('mid-roll-1-ad-1', 999000, []),
      _period('p1', 2000, [_adaptation(lang='nl', reps=[_rep('subs/P1.vtt')])]),
    ])

    def fake_get(url):
      if url.endswith('P0.vtt'):
        return SimpleNamespace(text=_vtt('00:00:00.000'), raise_for_status=lambda: None)
      if url.endswith('P1.vtt'):
        return SimpleNamespace(text=_vtt('00:00:00.000'), raise_for_status=lambda: None)
      raise AssertionError(f'unexpected url {url}')

    with patch('src.utils.download_subs_mpd.requests.get', side_effect=fake_get):
      files = download_subs_mpd(
        mpd=mpd,
        filename='Episode',
        platform=SimpleNamespace(value='GOPLAY'),
        ignore_periods=['^mid-roll.*'],
      )

    content = open(files[0], encoding='utf-8').read()
    # the 999s mid-roll is ignored, so the second cue is shifted by only 1s
    assert '00:00:01,000 --> 00:00:02,000' in content
