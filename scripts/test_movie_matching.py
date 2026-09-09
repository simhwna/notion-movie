import math
import os
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, Mock, patch
from movie_matching import (
    chart_index, title_index, normalize_imdb_id, property_text,
    resolve_movie, update_payload, sync_notion, imdb_property,
)

A = 'tt0000001'
B = 'tt0000002'
OUTSIDE = 'tt0000003'
ENTRIES = [dict(rank=1, imdbId=A, title='First film', titleKo='첫 영화', rating=8.5),
           dict(rank=2, imdbId=B, title='Second film', titleKo='다른 영화', rating=8.0)]
SCHEMA = {'제목': {'type': 'title'}, 'IMDb 순위 숫자': {'type': 'number'},
          'IMDb 평점': {'type': 'number'}, 'IMDb ID': {'type': 'rich_text'}}
NAMES = ('IMDb 순위 숫자', 'IMDb 평점', 'IMDb ID')


def props(raw_id='', title='첫 영화', rank=10, rating=6.0):
    return {'제목': {'title': [{'plain_text': title}]},
            'IMDb ID': {'rich_text': [{'plain_text': raw_id}]} if raw_id else {'rich_text': []},
            'IMDb 순위 숫자': {'number': rank}, 'IMDb 평점': {'number': rating}}


class MatchingTests(unittest.TestCase):
    def setUp(self):
        self.ids = chart_index(ENTRIES, 2)
        self.titles = title_index(self.ids)
        self.lookup = Mock(return_value=[])

    def match(self, raw_id='', title='첫 영화'):
        return resolve_movie(raw_id, title, self.ids, self.titles, self.lookup)

    def test_plain_id_normalizes_case_without_losing_zeroes(self):
        self.assertEqual(A, normalize_imdb_id('  TT0000001  '))

    def test_imdb_url_forms(self):
        for raw in ['https://www.imdb.com/title/' + A + '/?ref_=x',
                    'https://m.imdb.com/title/' + A + '/ratings',
                    'imdb.com/title/' + A + '/', '/title/' + A + '/']:
            with self.subTest(raw=raw):
                self.assertEqual(A, normalize_imdb_id(raw))

    def test_invalid_foreign_or_multiple_ids_rejected(self):
        for raw in ['tt123', '0tt0000001', A + B, A + ' ' + B,
                    'https://evil.example/title/' + A,
                    'https://imdb.com.evil.example/title/' + A,
                    'https://user@imdb.com/title/' + A, 'IMDb: ' + A, None]:
            with self.subTest(raw=raw):
                self.assertIsNone(normalize_imdb_id(raw))

    def test_existing_id_wins_over_conflicting_title(self):
        match = self.match(B, '첫 영화')
        self.assertEqual(B, match.imdb_id)
        self.assertEqual(2, match.entry['rank'])
        self.assertEqual('id', match.method)
        self.lookup.assert_not_called()

    def test_outside_chart_id_never_matches_remake_title(self):
        match = self.match(OUTSIDE, '첫 영화')
        self.assertEqual('outside_chart', match.status)
        self.assertEqual(OUTSIDE, match.imdb_id)
        self.assertIsNone(match.entry)
        self.lookup.assert_not_called()

    def test_invalid_populated_id_blocks_title_fallback(self):
        match = self.match('tt123', '첫 영화')
        self.assertEqual('invalid_id', match.status)
        self.lookup.assert_not_called()

    def test_empty_id_allows_unique_title(self):
        match = self.match()
        self.assertEqual(A, match.imdb_id)
        self.assertEqual('title', match.method)

    def test_same_title_candidates_are_ambiguous(self):
        self.ids[B]['titleKo'] = '첫 영화'
        self.titles = title_index(self.ids)
        self.assertEqual('ambiguous', self.match().status)
        self.lookup.assert_not_called()

    def test_multiple_row_title_forms_cannot_choose_different_films(self):
        self.ids[B]['titleKo'] = '첫 영화 2000'
        self.titles = title_index(self.ids)
        self.assertEqual('ambiguous', self.match(title='첫 영화 2000').status)

    def test_multiple_wikidata_ids_never_take_first_chart_hit(self):
        self.lookup.return_value = [OUTSIDE, A]
        self.assertEqual('ambiguous', self.match(title='미등록 제목').status)

    def test_unique_wikidata_id_can_match(self):
        self.lookup.return_value = [B, B.upper()]
        match = self.match(title='미등록 제목')
        self.assertEqual(B, match.imdb_id)
        self.assertEqual('wikidata', match.method)

    def test_unique_wikidata_outside_chart_keeps_its_id(self):
        self.lookup.return_value = [OUTSIDE]
        self.assertEqual('outside_chart', self.match(title='미등록 제목').status)

    def test_unknown_title_remains_unresolved(self):
        self.assertEqual('unresolved', self.match(title='미등록 제목').status)

    def test_blank_title_can_still_use_existing_id(self):
        self.assertEqual(B, self.match(B, '').imdb_id)

    def test_property_text_supports_url_and_rich_text_content(self):
        self.assertEqual(A, property_text({'rich_text': [{'text': {'content': A}}]}))
        self.assertEqual('https://www.imdb.com/title/' + A + '/', property_text({'url': 'https://www.imdb.com/title/' + A + '/'}))

    def test_property_alias_and_type_selection(self):
        self.assertEqual('IMDb ID', imdb_property(SCHEMA))
        self.assertEqual('IMDb 링크', imdb_property({'IMDb 링크': {'type': 'url'}}))
        self.assertIsNone(imdb_property({'IMDb 평점': {'type': 'number'}}))

    def test_blocked_or_unresolved_rows_preserve_all_values(self):
        omdb = Mock()
        for match in [self.match('tt123'), self.match(title='미등록 제목')]:
            self.assertEqual({}, update_payload(match, props(), SCHEMA, NAMES, '', omdb))
        omdb.assert_not_called()

    def test_outside_chart_clears_only_rank_and_queries_same_id(self):
        omdb = Mock(return_value=7.2)
        match = self.match(OUTSIDE)
        payload = update_payload(match, props(OUTSIDE), SCHEMA, NAMES, OUTSIDE, omdb)
        self.assertEqual({'number': None}, payload['IMDb 순위 숫자'])
        self.assertEqual({'number': 7.2}, payload['IMDb 평점'])
        self.assertNotIn('IMDb ID', payload)
        omdb.assert_called_once_with(OUTSIDE)

    def test_rating_fetch_failure_does_not_clear_existing_rating(self):
        payload = update_payload(self.match(OUTSIDE), props(OUTSIDE), SCHEMA, NAMES, OUTSIDE, lambda _: None)
        self.assertNotIn('IMDb 평점', payload)

    def test_bad_ratings_not_written(self):
        for value in [float('nan'), float('inf'), -1, 11, True]:
            with self.subTest(value=value):
                payload = update_payload(self.match(OUTSIDE), props(OUTSIDE), SCHEMA, NAMES, OUTSIDE, lambda _: value)
                self.assertNotIn('IMDb 평점', payload)

    def test_empty_text_id_backfilled(self):
        payload = update_payload(self.match(), props(), SCHEMA, NAMES, '', lambda _: None)
        self.assertEqual(A, payload['IMDb ID']['rich_text'][0]['text']['content'])

    def test_empty_url_id_backfilled(self):
        schema = dict(SCHEMA, **{'IMDb ID': {'type': 'url'}})
        payload = update_payload(self.match(), props(), schema, NAMES, '', lambda _: None)
        self.assertEqual('https://www.imdb.com/title/' + A + '/', payload['IMDb ID']['url'])

    def test_existing_id_is_never_rewritten(self):
        raw = 'HTTPS://WWW.IMDB.COM/title/' + B + '/'
        payload = update_payload(self.match(raw), props(raw), SCHEMA, NAMES, raw, lambda _: None)
        self.assertNotIn('IMDb ID', payload)

    def test_idempotent_matching_row_has_no_patch(self):
        payload = update_payload(self.match(A), props(A, rank=1, rating=8.5), SCHEMA, NAMES, A, lambda _: None)
        self.assertEqual({}, payload)

    def test_incomplete_chart_is_rejected(self):
        with self.assertRaises(ValueError):
            chart_index(ENTRIES, 250)

    def test_duplicate_chart_id_or_rank_is_rejected(self):
        for key, value in [('imdbId', A), ('rank', 1), ('rank', True), ('title', '')]:
            with self.subTest(key=key):
                entries = [ENTRIES[0], dict(ENTRIES[1], **{key: value})]
                with self.assertRaises(ValueError):
                    chart_index(entries, 2)

    def test_sync_adapter_uses_id_priority_without_live_requests(self):
        rows = [dict(id='local-a', properties=props(B)),
                dict(id='local-b', properties=props(OUTSIDE)),
                dict(id='local-c', properties=props('invalid')),
                dict(id='local-d', properties=props())]
        client = MagicMock()
        factory = Mock(return_value=client)
        api = SimpleNamespace(
            EXPECTED=2, log=Mock(), notion_client=factory,
            load_schema=Mock(return_value=SCHEMA), query_rows=Mock(return_value=rows),
            pick_property=lambda schema, kinds, tokens: next((name for name, spec in schema.items() if spec['type'] in kinds and all(token in name.lower().replace(' ', '') for token in tokens)), None),
            httpx=SimpleNamespace(Client=factory), WD_API_HEADERS={}, WD_MAX_LOOKUPS=120,
            WD_GAP=0, OMDB_GAP=0, OMDB_MAX_CALLS=200, time=SimpleNamespace(sleep=Mock()),
            wikidata_lookup=Mock(return_value=[]), fetch_omdb_rating=Mock(return_value=7.2),
            patch_page=Mock(return_value=True),
        )
        with patch.dict(os.environ, {'NOTION_TOKEN':'fixture-token','NOTION_DATA_SOURCE_ID':'fixture-source','OMDB_API_KEY':'fixture-key'}):
            report = sync_notion(ENTRIES, api)
        self.assertEqual(1, report['matchedById'])
        self.assertEqual(1, report['matchedByTitle'])
        self.assertEqual(1, report['outsideChart'])
        self.assertEqual(1, report['invalidId'])
        self.assertEqual(3, report['updated'])
        self.assertNotIn('첫 영화', str(report))
        calls = api.patch_page.call_args_list
        self.assertEqual(['local-a','local-b','local-d'], [call.args[1] for call in calls])
        self.assertEqual({'number':2}, calls[0].args[2]['IMDb 순위 숫자'])
        self.assertEqual({'number':None}, calls[1].args[2]['IMDb 순위 숫자'])
        api.wikidata_lookup.assert_not_called()
        self.assertEqual(OUTSIDE, api.fetch_omdb_rating.call_args.args[1])


if __name__ == '__main__':
    unittest.main()
