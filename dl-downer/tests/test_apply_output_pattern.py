import os
import pytest
from unittest.mock import patch

from src.utils.apply_output_pattern import (
  apply_output_pattern,
  _resolve_segment,
  _substitute_variables,
)


def p(*parts):
  '''Normalize a path for cross-platform assertions.'''
  return os.path.normpath(os.path.join(*parts))


# ──────────────────────────────────────────────────────
# _substitute_variables
# ──────────────────────────────────────────────────────

class TestSubstituteVariables:

  def test_all_variables_resolved(self):
    result = _substitute_variables(
      '{title}.S{season}E{episode}',
      {'title': 'De.Mol', 'season': '01', 'episode': '03'},
    )
    assert result == 'De.Mol.S01E03'

  def test_missing_variable_left_as_placeholder(self):
    result = _substitute_variables(
      'S{season}E{episode}',
      {'season': '01'},
    )
    assert result == 'S01E{episode}'

  def test_no_variables(self):
    result = _substitute_variables('literal_text', {'title': 'whatever'})
    assert result == 'literal_text'

  def test_empty_string(self):
    result = _substitute_variables('', {'title': 'x'})
    assert result == ''


# ──────────────────────────────────────────────────────
# _resolve_segment
# ──────────────────────────────────────────────────────

class TestResolveSegment:

  def test_all_resolved(self):
    variables = {'title': 'De.Mol', 'season': '01', 'episode': '03', 'extension': 'mkv'}
    result = _resolve_segment('{title}.S{season}E{episode}.{extension}', variables)
    assert result == 'De.Mol.S01E03.mkv'

  def test_season_episode_stripped_when_missing(self):
    variables = {'title': 'Some.Movie', 'extension': 'mkv'}
    result = _resolve_segment('{title}.S{season}E{episode}.{extension}', variables)
    assert result == 'Some.Movie.mkv'

  def test_only_title_and_extension(self):
    variables = {'title': 'Test', 'extension': 'mp4'}
    result = _resolve_segment('{title}.{extension}', variables)
    assert result == 'Test.mp4'

  def test_platform_segment(self):
    variables = {'platform': 'VRTMAX'}
    result = _resolve_segment('{platform}', variables)
    assert result == 'VRTMAX'

  def test_entirely_unresolved(self):
    result = _resolve_segment('{unknown}', {})
    assert result == ''

  def test_mixed_resolved_and_unresolved(self):
    variables = {'title': 'Show', 'extension': 'mkv'}
    result = _resolve_segment('{title}.{missing_var}.{extension}', variables)
    assert result == 'Show.mkv'

  def test_episode_only_no_season(self):
    '''S{season}E05 still contains {season}, so the whole dot-group is stripped.'''
    variables = {'title': 'Test', 'episode': '05', 'extension': 'mkv'}
    result = _resolve_segment('{title}.S{season}E{episode}.{extension}', variables)
    assert result == 'Test.mkv'


# ──────────────────────────────────────────────────────
# apply_output_pattern (integration tests)
# ──────────────────────────────────────────────────────

class TestApplyOutputPattern:

  @patch.dict(os.environ, {
    'DOWNLOADS_FOLDER': '/downloads',
    'DL_OUTPUT_PATTERN': '{platform}/{title}.S{season}E{episode}.{extension}',
  })
  def test_default_pattern_with_series(self):
    result = apply_output_pattern(
      title='De Mol',
      platform='VRTMAX',
      extension='mkv',
      suggested_filepath='/downloads/VRTMAX/De.Mol.S01E03.mkv',
      current_filepath='/downloads/VRTMAX/De.Mol.S01E03.mkv',
      season='01',
      episode='03',
    )
    assert result == p('/downloads', 'VRTMAX', 'De.Mol.S01E03.mkv')

  @patch.dict(os.environ, {
    'DOWNLOADS_FOLDER': '/downloads',
    'DL_OUTPUT_PATTERN': '{platform}/{title}.S{season}E{episode}.{extension}',
  })
  def test_default_pattern_without_season_episode(self):
    result = apply_output_pattern(
      title='Some Movie Title',
      platform='VRTMAX',
      extension='mkv',
      suggested_filepath='/downloads/VRTMAX/Some.Movie.Title.mkv',
    )
    assert result == p('/downloads', 'VRTMAX', 'Some.Movie.Title.mkv')

  @patch.dict(os.environ, {
    'DOWNLOADS_FOLDER': '/downloads',
    'DL_OUTPUT_PATTERN': '{platform}/{title}.S{season}E{episode}.{extension}',
  })
  def test_goplay_no_season_episode(self):
    result = apply_output_pattern(
      title='Huis Gemaakt',
      platform='GOPLAY',
      extension='mp4',
      suggested_filepath='/downloads/GOPLAY/Huis.Gemaakt.mp4',
    )
    assert result == p('/downloads', 'GOPLAY', 'Huis.Gemaakt.mp4')

  @patch.dict(os.environ, {
    'DOWNLOADS_FOLDER': './downloads',
    'DL_OUTPUT_PATTERN': '{platform}/{title}/{title}.S{season}E{episode}.{extension}',
  })
  def test_nested_subdirectory_pattern(self):
    result = apply_output_pattern(
      title='De Mol',
      platform='VRTMAX',
      extension='mkv',
      suggested_filepath='./downloads/VRTMAX/De.Mol.S01E03.mkv',
      season='01',
      episode='03',
    )
    assert result == p('./downloads', 'VRTMAX', 'De.Mol', 'De.Mol.S01E03.mkv')

  @patch.dict(os.environ, {
    'DOWNLOADS_FOLDER': './downloads',
    'DL_OUTPUT_PATTERN': '{platform}/{title}/{title}.S{season}E{episode}.{extension}',
  })
  def test_nested_subdirectory_pattern_movie(self):
    result = apply_output_pattern(
      title='A Movie',
      platform='VRTMAX',
      extension='mkv',
      suggested_filepath='./downloads/VRTMAX/A.Movie.mkv',
    )
    assert result == p('./downloads', 'VRTMAX', 'A.Movie', 'A.Movie.mkv')

  @patch.dict(os.environ, {
    'DOWNLOADS_FOLDER': '/data/media',
    'DL_OUTPUT_PATTERN': '{title}.S{season}E{episode}.{extension}',
  })
  def test_flat_pattern_no_platform_folder(self):
    result = apply_output_pattern(
      title='Show Name',
      platform='VTMGO',
      extension='mkv',
      suggested_filepath='/data/media/VTMGO/Show.Name.S02E10.mkv',
      season='02',
      episode='10',
    )
    assert result == p('/data/media', 'Show.Name.S02E10.mkv')

  @patch.dict(os.environ, {
    'DOWNLOADS_FOLDER': '/downloads',
    'DL_OUTPUT_PATTERN': '{platform}/{title}.S{season}E{episode}.{extension}',
  })
  def test_special_characters_in_title(self):
    result = apply_output_pattern(
      title="Café & Bar: L'été",
      platform='VRTMAX',
      extension='mkv',
      suggested_filepath='/downloads/VRTMAX/Cafe.En.Bar.Lete.S01E01.mkv',
      season='01',
      episode='01',
    )
    assert 'Cafe' in result
    assert '.mkv' in result
    assert 'S01E01' in result
    assert '{' not in result

  @patch.dict(os.environ, {
    'DOWNLOADS_FOLDER': '/downloads',
    'DL_OUTPUT_PATTERN': '{platform}/{title}.S{season}E{episode}.{extension}',
  })
  def test_youtube_no_season(self):
    result = apply_output_pattern(
      title='Some YouTube Video',
      platform='YOUTUBE',
      extension='mkv',
      suggested_filepath='/downloads/YOUTUBE/Some.Youtube.Video.mkv',
    )
    assert result == p('/downloads', 'YOUTUBE', 'Some.Youtube.Video.mkv')

  @patch.dict(os.environ, {
    'DOWNLOADS_FOLDER': '/downloads',
    'DL_OUTPUT_PATTERN': '{platform}/{title}.{extension}',
  })
  def test_simple_pattern_ignores_season_episode(self):
    result = apply_output_pattern(
      title='De Mol',
      platform='VRTMAX',
      extension='mkv',
      suggested_filepath='/downloads/VRTMAX/De.Mol.S01E03.mkv',
      season='01',
      episode='03',
    )
    assert result == p('/downloads', 'VRTMAX', 'De.Mol.mkv')

  @patch.dict(os.environ, {
    'DOWNLOADS_FOLDER': '/downloads',
  }, clear=False)
  def test_default_pattern_when_env_not_set(self):
    env = os.environ.copy()
    env.pop('DL_OUTPUT_PATTERN', None)
    with patch.dict(os.environ, env, clear=True):
      result = apply_output_pattern(
        title='Test Show',
        platform='VRTMAX',
        extension='mkv',
        suggested_filepath='/downloads/VRTMAX/Test.Show.S01E05.mkv',
        season='01',
        episode='05',
      )
      assert 'S01E05' in result
      assert 'VRTMAX' in result

  @patch.dict(os.environ, {
    'DOWNLOADS_FOLDER': '/downloads',
    'DL_OUTPUT_PATTERN': '{platform}/{title}.S{season}E{episode}.{extension}',
  })
  def test_file_deduplication(self, tmp_path):
    with patch.dict(os.environ, {'DOWNLOADS_FOLDER': str(tmp_path)}):
      target_dir = tmp_path / 'VRTMAX'
      target_dir.mkdir()
      (target_dir / 'De.Mol.S01E03.mkv').touch()

      result = apply_output_pattern(
        title='De Mol',
        platform='VRTMAX',
        extension='mkv',
        suggested_filepath='/tmp/VRTMAX/De.Mol.S01E03.mkv',
        season='01',
        episode='03',
      )
      assert 'De.Mol.S01E03-' in result
      assert result.endswith('.mkv')

  @patch.dict(os.environ, {
    'DOWNLOADS_FOLDER': '/downloads',
    'DL_OUTPUT_PATTERN': '{platform}/{title}.S{season}E{episode}.{extension}',
  })
  def test_zero_padded_season_episode(self):
    result = apply_output_pattern(
      title='Show',
      platform='VRTMAX',
      extension='mkv',
      suggested_filepath='/downloads/VRTMAX/Show.S01E09.mkv',
      season='01',
      episode='09',
    )
    assert 'S01E09' in result

  @patch.dict(os.environ, {
    'DOWNLOADS_FOLDER': '/downloads',
    'DL_OUTPUT_PATTERN': 'all/{title}.{extension}',
  })
  def test_custom_pattern_no_platform(self):
    result = apply_output_pattern(
      title='Anything',
      platform='GOPLAY',
      extension='mkv',
      suggested_filepath='/downloads/GOPLAY/Anything.mkv',
    )
    assert result == p('/downloads', 'all', 'Anything.mkv')

  @patch.dict(os.environ, {
    'DOWNLOADS_FOLDER': '/downloads',
    'DL_OUTPUT_PATTERN': '{platform}/{title}.S{season}E{episode}.720p.{extension}',
  })
  def test_extra_literal_in_filename(self):
    result = apply_output_pattern(
      title='Show',
      platform='VRTMAX',
      extension='mkv',
      suggested_filepath='/downloads/VRTMAX/Show.S01E01.mkv',
      season='01',
      episode='01',
    )
    assert result == p('/downloads', 'VRTMAX', 'Show.S01E01.720p.mkv')

  @patch.dict(os.environ, {
    'DOWNLOADS_FOLDER': '/downloads',
    'DL_OUTPUT_PATTERN': '{platform}/{title}.S{season}E{episode}.720p.{extension}',
  })
  def test_extra_literal_without_season(self):
    result = apply_output_pattern(
      title='Movie',
      platform='VRTMAX',
      extension='mkv',
      suggested_filepath='/downloads/VRTMAX/Movie.mkv',
    )
    assert result == p('/downloads', 'VRTMAX', 'Movie.720p.mkv')

  # ── Path traversal / security ──

  @patch.dict(os.environ, {
    'DOWNLOADS_FOLDER': '/downloads',
    'DL_OUTPUT_PATTERN': '../{title}.{extension}',
  })
  def test_path_traversal_blocked_dotdot(self):
    result = apply_output_pattern(
      title='Hack',
      platform='VRTMAX',
      extension='mkv',
      suggested_filepath='/downloads/VRTMAX/Hack.mkv',
    )
    assert result == '/downloads/VRTMAX/Hack.mkv'

  @patch.dict(os.environ, {
    'DOWNLOADS_FOLDER': '/downloads',
    'DL_OUTPUT_PATTERN': '{platform}/../../etc/{title}.{extension}',
  })
  def test_path_traversal_blocked_nested_dotdot(self):
    result = apply_output_pattern(
      title='Hack',
      platform='VRTMAX',
      extension='mkv',
      suggested_filepath='/downloads/VRTMAX/Hack.mkv',
    )
    assert result == '/downloads/VRTMAX/Hack.mkv'

  @patch.dict(os.environ, {
    'DOWNLOADS_FOLDER': '/downloads',
    'DL_OUTPUT_PATTERN': '{platform}/{title}..{extension}',
  })
  def test_dotdot_in_filename_part_blocked(self):
    result = apply_output_pattern(
      title='Test',
      platform='VRTMAX',
      extension='mkv',
      suggested_filepath='/downloads/VRTMAX/Test.mkv',
    )
    assert result == '/downloads/VRTMAX/Test.mkv'

  # ── Fallback ──

  @patch.dict(os.environ, {
    'DOWNLOADS_FOLDER': '/downloads',
    'DL_OUTPUT_PATTERN': '{nonexistent_var}/{another_missing}',
  })
  def test_pattern_resolves_to_empty_uses_fallback(self):
    result = apply_output_pattern(
      title='Fallback Test',
      platform='GOPLAY',
      extension='mkv',
      suggested_filepath='/downloads/GOPLAY/Fallback.Test.mkv',
    )
    assert result == '/downloads/GOPLAY/Fallback.Test.mkv'
