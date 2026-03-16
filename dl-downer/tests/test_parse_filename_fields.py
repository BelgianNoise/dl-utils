from src.utils.parse_filename_fields import parse_filename_fields


class TestParseFilenameFields:

  # ── S##E## patterns ──

  def test_standard_s01e03(self):
    result = parse_filename_fields('De.Mol.S01E03')
    assert result['title'] == 'De.Mol'
    assert result['season'] == '01'
    assert result['episode'] == '03'

  def test_uppercase_s2e5(self):
    result = parse_filename_fields('Show.S2E5.720p')
    assert result['title'] == 'Show'
    assert result['season'] == '02'
    assert result['episode'] == '05'

  def test_lowercase_s01e01(self):
    result = parse_filename_fields('show.s01e01')
    assert result['title'] == 'show'
    assert result['season'] == '01'
    assert result['episode'] == '01'

  def test_dot_between_s_and_e(self):
    result = parse_filename_fields('Show.S01.E03')
    assert result['title'] == 'Show'
    assert result['season'] == '01'
    assert result['episode'] == '03'

  def test_space_separated(self):
    result = parse_filename_fields('Some Show S1E2')
    assert result['title'] == 'Some Show'
    assert result['season'] == '01'
    assert result['episode'] == '02'

  def test_dash_before_season(self):
    result = parse_filename_fields('Show-S03E10')
    assert result['title'] == 'Show'
    assert result['season'] == '03'
    assert result['episode'] == '10'

  def test_zero_padded_result(self):
    result = parse_filename_fields('X.S1E3')
    assert result['season'] == '01'
    assert result['episode'] == '03'

  # ── Dutch S##A## format ──

  def test_dutch_s_a_format(self):
    result = parse_filename_fields('De.Mol.S01A03')
    assert result['title'] == 'De.Mol'
    assert result['season'] == '01'
    assert result['episode'] == '03'

  # ── 1x03 pattern ──

  def test_1x03_format(self):
    result = parse_filename_fields('Show.1x03')
    assert result['title'] == 'Show'
    assert result['season'] == '01'
    assert result['episode'] == '03'

  def test_2x10_format_with_dashes(self):
    result = parse_filename_fields('Show-2x10-720p')
    assert result['title'] == 'Show'
    assert result['season'] == '02'
    assert result['episode'] == '10'

  # ── Written-out patterns ──

  def test_season_episode_written_out(self):
    result = parse_filename_fields('Show Season 1 Episode 3')
    assert result['title'] == 'Show'
    assert result['season'] == '01'
    assert result['episode'] == '03'

  def test_seizoen_aflevering(self):
    result = parse_filename_fields('De Mol Seizoen 2 Aflevering 5')
    assert result['title'] == 'De Mol'
    assert result['season'] == '02'
    assert result['episode'] == '05'

  def test_season_ep_abbreviated(self):
    result = parse_filename_fields('Show.Season.3.Ep.12')
    assert result['title'] == 'Show'
    assert result['season'] == '03'
    assert result['episode'] == '12'

  # ── No season/episode ──

  def test_no_season_episode(self):
    result = parse_filename_fields('Just.A.Movie.2024')
    assert result['title'] == 'Just.A.Movie.2024'
    assert result['season'] is None
    assert result['episode'] is None

  def test_plain_title(self):
    result = parse_filename_fields('Documentary')
    assert result['title'] == 'Documentary'
    assert result['season'] is None
    assert result['episode'] is None

  def test_timestamp_filename(self):
    result = parse_filename_fields('20240315-143022')
    assert result['title'] == '20240315-143022'
    assert result['season'] is None
    assert result['episode'] is None

  # ── Edge cases ──

  def test_multi_digit_season_episode(self):
    result = parse_filename_fields('Show.S12E103')
    assert result['season'] == '12'
    assert result['episode'] == '103'

  def test_title_extraction_strips_trailing_separators(self):
    result = parse_filename_fields('Show...S01E01')
    assert result['title'] == 'Show'
    assert result['season'] == '01'
    assert result['episode'] == '01'

  def test_empty_string(self):
    result = parse_filename_fields('')
    assert result['title'] == ''
    assert result['season'] is None
    assert result['episode'] is None
