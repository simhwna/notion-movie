#!/usr/bin/env python3
'''IMDb Top 250을 갱신해 data/top250.json에 저장하고 노션 Movies DB의 순위와 평점을 맞춘다.

수집 우선순위
  1. imdb.com/chart/top 의 JSON-LD, __NEXT_DATA__, DOM
  2. top250.info/charts 표

한국어 제목은 위키데이터 SPARQL 로 IMDb ID 별 ko 라벨과 ko 별칭을 받아서 총읍한다.
제목으로 짝을 못 찾은 노션 행은 위키데이터 검색 API 로 되짚어 IMDb ID 를 찾는다.

사운 끝에 data/sync-report.json 에 맞춘 결과와 남은 행 목록을 쓰고 원경에 올린다.

환경 변수
  NOTION_TOKEN           노션 내부 통합 토큰
  NOTION_DATA_SOURCE_ID  Movies DB 의 data source id
  OMDB_API_KEY           OMDb 키. 없으면 차트에 없는 영화의 평점 조회를 건너뛴다

250건을 얻지 못하면 파일을 덮어쓰지 않고 종료 코드 1로 끝난다.
'''
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

IMDB_CHART_URL = 'https://www.imdb.com/chart/top/'
INFO_CHART_URLS = ('https://top250.info/charts', 'http://top250.info/charts')
OMDB_URL = 'https://www.omdbapi.com/'
WIKIDATA_URL = 'https://query.wikidata.org/sparql'
WIKIDATA_API = 'https://www.wikidata.org/w/api.php'
WIKIDATA_CHUNK = 125
OUT_PATH = Path('data/top250.json')
REPORT_PATH = Path('data/sync-report.json')
NOTION_API = 'https://api.notion.com/v1'
NOTION_VERSION = '2025-09-03'
NOTION_GAP = 0.4
OMDB_GAP = 0.25
OMDB_MAX_CALLS = 200
WD_GAP = 0.3
WD_MAX_LOOKUPS = 120
EXPECTED = 250
FAIL_LOG_LIMIT = 5
CACHE_KEYS = ('rank', 'imdbId', 'title', 'rating', 'titleKo')


def hangul(cho, jung, jong=0):
    return chr(0xAC00 + (cho * 21 + jung) * 28 + jong)


HANGUL_RANGE = chr(0xAC00) + '-' + chr(0xD7A3)
TOKEN_RANK = hangul(9, 13, 4) + hangul(11, 16)
TOKEN_RATING = hangul(17, 6, 21) + hangul(12, 4, 16)
NORMALIZE_RE = re.compile('[^0-9a-z' + HANGUL_RANGE + ']+')

BROWSER_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

WIKIDATA_HEADERS = {
    'User-Agent': 'notion-movie/1.0 (https://github.com/simhwna/notion-movie)',
    'Accept': 'application/sparql-results+json',
}

WD_API_HEADERS = {
    'User-Agent': 'notion-movie/1.0 (https://github.com/simhwna/notion-movie)',
    'Accept': 'application/json',
}

fail_logged = 0


def log(message):
    print(message, flush=True)


def fetch_html(url):
    try:
        with httpx.Client(headers=BROWSER_HEADERS, timeout=30.0, follow_redirects=True) as client:
            response = client.get(url)
    except httpx.HTTPError as error:
        log('http fail {0} {1}'.format(url, error))
        return None
    log('http {0} status {1} size {2}'.format(url, response.status_code, len(response.text)))
    if response.status_code != 200:
        return None
    return response.text


def imdb_id_from_url(url):
    match = re.search(r'(tt\d{5,})', url or '')
    return match.group(1) if match else None


def to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_json_ld(soup):
    entries = []
    for tag in soup.find_all('script', attrs={'type': 'application/ld+json'}):
        raw = tag.string or tag.get_text()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        items = data.get('itemListElement') if isinstance(data, dict) else None
        if not isinstance(items, list):
            continue
        for index, element in enumerate(items, start=1):
            if not isinstance(element, dict):
                continue
            item = element.get('item')
            if not isinstance(item, dict):
                continue
            imdb_id = imdb_id_from_url(item.get('url', ''))
            if not imdb_id:
                continue
            aggregate = item.get('aggregateRating')
            rating = to_float(aggregate.get('ratingValue')) if isinstance(aggregate, dict) else None
            position = element.get('position')
            entries.append({
                'rank': position if isinstance(position, int) else index,
                'imdbId': imdb_id,
                'title': item.get('name'),
                'rating': rating,
            })
        if entries:
            break
    return entries


def parse_next_data(soup):
    tag = soup.find('script', attrs={'id': '__NEXT_DATA__'})
    if tag is None:
        return []
    raw = tag.string or tag.get_text()
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return []

    found = []

    def visit(node):
        if isinstance(node, dict):
            rank = node.get('currentRank')
            inner = node.get('node') if isinstance(node.get('node'), dict) else node
            imdb_id = inner.get('id') if isinstance(inner.get('id'), str) else None
            if isinstance(rank, int) and imdb_id and imdb_id.startswith('tt'):
                title_text = inner.get('titleText')
                summary = inner.get('ratingsSummary')
                found.append({
                    'rank': rank,
                    'imdbId': imdb_id,
                    'title': title_text.get('text') if isinstance(title_text, dict) else None,
                    'rating': to_float(summary.get('aggregateRating')) if isinstance(summary, dict) else None,
                })
            for value in node.values():
                visit(value)
        elif isinstance(node, list):
            for value in node:
                visit(value)

    visit(data)
    return found


def parse_dom(soup):
    entries = []
    seen = set()
    for anchor in soup.select('a[href*="/title/tt"]'):
        imdb_id = imdb_id_from_url(anchor.get('href', ''))
        if not imdb_id or imdb_id in seen:
            continue
        text = anchor.get_text(' ', strip=True)
        if not text:
            continue
        seen.add(imdb_id)
        entries.append({
            'rank': len(entries) + 1,
            'imdbId': imdb_id,
            'title': re.sub(r'^\d+\.\s*', '', text),
            'rating': None,
        })
    return entries


def parse_top250_info(html):
    soup = BeautifulSoup(html, 'html.parser')
    entries = []
    seen = set()
    for row in soup.find_all('tr'):
        link = row.find('a', href=re.compile(r'/movie/\?\d+'))
        if link is None:
            continue
        match = re.search(r'/movie/\?(\d+)', link.get('href', ''))
        if match is None:
            continue
        number = match.group(1)
        imdb_id = 'tt' + (number if len(number) >= 7 else number.zfill(7))
        if imdb_id in seen:
            continue
        rank = None
        rating = None
        for cell in row.find_all('td'):
            text = cell.get_text(' ', strip=True)
            if rank is None and re.fullmatch(r'\d{1,3}', text):
                rank = int(text)
                continue
            if rating is None and re.fullmatch(r'\d{1,2}\.\d', text):
                rating = float(text)
        if rank is None:
            continue
        title = re.sub(r'\s*\(\d{4}\)\s*$', '', link.get_text(' ', strip=True))
        seen.add(imdb_id)
        entries.append({'rank': rank, 'imdbId': imdb_id, 'title': title, 'rating': rating})
    return entries


def dedupe(entries):
    best = {}
    for entry in entries:
        current = best.get(entry['imdbId'])
        if current is None or entry['rank'] < current['rank']:
            best[entry['imdbId']] = entry
    ordered = sorted(best.values(), key=lambda item: item['rank'])
    for position, entry in enumerate(ordered, start=1):
        entry['rank'] = position
    return ordered


def collect_from_imdb():
    html = fetch_html(IMDB_CHART_URL)
    if not html:
        return []
    soup = BeautifulSoup(html, 'html.parser')
    parsers = (('JSON-LD', parse_json_ld), ('NEXT_DATA', parse_next_data), ('DOM', parse_dom))
    for name, parser in parsers:
        found = dedupe(parser(soup))
        log('imdb {0} parsed {1}'.format(name, len(found)))
        if name == 'DOM' and len(found) > EXPECTED:
            found = dedupe(found[:EXPECTED])
            log('dom trimmed to 250')
        if len(found) == EXPECTED:
            return found
    return []


def collect_from_info():
    for url in INFO_CHART_URLS:
        html = fetch_html(url)
        if not html:
            continue
        found = dedupe(parse_top250_info(html))
        log('top250.info parsed {0}'.format(len(found)))
        if len(found) == EXPECTED:
            return found
    return []


def collect_chart():
    found = collect_from_imdb()
    if found:
        log('chart source imdb ok 250')
        return found
    log('imdb source failed, switching to fallback')
    found = collect_from_info()
    if found:
        log('chart source top250.info ok 250')
        return found
    raise SystemExit('could not collect 250 entries, keeping the old cache file')


def fetch_ko_titles(entries):
    labels = {}
    alts = {}
    ids = [entry['imdbId'] for entry in entries]
    for start in range(0, len(ids), WIKIDATA_CHUNK):
        chunk = ids[start:start + WIKIDATA_CHUNK]
        values = ' '.join('"' + imdb_id + '"' for imdb_id in chunk)
        query = (
            'SELECT ?imdb ?label ?alt WHERE { VALUES ?imdb { ' + values + ' } '
            '?item wdt:P345 ?imdb . '
            'OPTIONAL { ?item rdfs:label ?label . FILTER(lang(?label) = "ko") } '
            'OPTIONAL { ?item skos:altLabel ?alt . FILTER(lang(?alt) = "ko") } }'
        )
        try:
            with httpx.Client(headers=WIKIDATA_HEADERS, timeout=90.0, follow_redirects=True) as client:
                response = client.post(WIKIDATA_URL, data={'query': query, 'format': 'json'})
            if response.status_code != 200:
                log('wikidata sparql status {0}'.format(response.status_code))
                continue
            rows = response.json().get('results', {}).get('bindings', [])
        except (httpx.HTTPError, ValueError) as error:
            log('wikidata sparql failed {0}'.format(error))
            continue
        for row in rows:
            imdb_id = row.get('imdb', {}).get('value')
            if not imdb_id:
                continue
            label = row.get('label', {}).get('value')
            if label and imdb_id not in labels:
                labels[imdb_id] = label
            alt = row.get('alt', {}).get('value')
            if alt:
                bucket = alts.setdefault(imdb_id, [])
                if alt not in bucket:
                    bucket.append(alt)
        time.sleep(1.0)
    log('ko labels {0}, entries with ko alias {1}'.format(len(labels), len(alts)))
    return labels, alts


def write_cache(entries):
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    trimmed = []
    for entry in entries:
        item = {}
        for key in CACHE_KEYS:
            if key in entry:
                item[key] = entry[key]
        trimmed.append(item)
    payload = json.dumps(trimmed, ensure_ascii=False, indent=2) + '\n'
    if OUT_PATH.exists() and OUT_PATH.read_text(encoding='utf-8') == payload:
        log('top250.json unchanged')
        return False
    OUT_PATH.write_text(payload, encoding='utf-8')
    log('top250.json written {0}'.format(len(trimmed)))
    return True


def notion_client(token):
    return httpx.Client(
        base_url=NOTION_API,
        headers={
            'Authorization': 'Bearer ' + token,
            'Notion-Version': NOTION_VERSION,
            'Content-Type': 'application/json',
        },
        timeout=30.0,
    )


def load_schema(client, data_source_id):
    response = client.get('/data_sources/' + data_source_id)
    response.raise_for_status()
    return response.json().get('properties', {})


def query_rows(client, data_source_id):
    rows = []
    cursor = None
    while True:
        payload = {'page_size': 100}
        if cursor:
            payload['start_cursor'] = cursor
        response = client.post('/data_sources/' + data_source_id + '/query', json=payload)
        response.raise_for_status()
        data = response.json()
        rows.extend(data.get('results', []))
        if not data.get('has_more'):
            return rows
        cursor = data.get('next_cursor')
        time.sleep(NOTION_GAP)


def plain_text(prop):
    if not isinstance(prop, dict):
        return ''
    if isinstance(prop.get('url'), str):
        return prop['url'].strip()
    parts = prop.get('rich_text') or prop.get('title') or []
    return ''.join(part.get('plain_text', '') for part in parts).strip()


def number_value(prop):
    return prop.get('number') if isinstance(prop, dict) else None


def normalize_key(value):
    return NORMALIZE_RE.sub('', (value or '').lower())


def pick_property(schema, kinds, tokens):
    for name in schema:
        definition = schema[name]
        if not isinstance(definition, dict) or definition.get('type') not in kinds:
            continue
        key = normalize_key(name)
        if all(token in key for token in tokens):
            return name
    return None


def normalize_title(value):
    return NORMALIZE_RE.sub('', (value or '').lower())


def entry_title_keys(entry):
    keys = []
    candidates = [entry.get('title'), entry.get('titleKo')]
    candidates.extend(entry.get('_koAlts') or [])
    for value in candidates:
        key = normalize_title(value)
        if key and key not in keys:
            keys.append(key)
    return keys


def row_title_keys(value):
    base = (value or '').strip()
    trimmed = re.sub(r'\s*[\(\[]?\d{4}[\)\]]?\s*$', '', base)
    keys = []
    for candidate in (base, trimmed):
        key = normalize_title(candidate)
        if key and key not in keys:
            keys.append(key)
    return keys


def title_key_counts(entries):
    counts = {}
    for entry in entries:
        for key in entry_title_keys(entry):
            counts[key] = counts.get(key, 0) + 1
    return counts


def unique_title_index(entries):
    counts = title_key_counts(entries)
    index = {}
    for entry in entries:
        for key in entry_title_keys(entry):
            if counts.get(key) == 1:
                index[key] = entry
    return index


def duplicate_keys(entries):
    counts = title_key_counts(entries)
    return sorted(key for key in counts if counts[key] > 1)


def wikidata_lookup(client, title):
    try:
        response = client.get(WIKIDATA_API, params={
            'action': 'wbsearchentities',
            'search': title,
            'language': 'ko',
            'uselang': 'ko',
            'type': 'item',
            'limit': 5,
            'format': 'json',
        })
        if response.status_code != 200:
            return []
        candidates = [item.get('id') for item in response.json().get('search', []) if item.get('id')]
    except (httpx.HTTPError, ValueError):
        return []
    if not candidates:
        return []
    try:
        detail = client.get(WIKIDATA_API, params={
            'action': 'wbgetentities',
            'ids': '|'.join(candidates),
            'props': 'claims',
            'format': 'json',
        })
        if detail.status_code != 200:
            return []
        entities = detail.json().get('entities', {})
    except (httpx.HTTPError, ValueError):
        return []
    found = []
    for qid in candidates:
        claims = (entities.get(qid) or {}).get('claims', {})
        for claim in claims.get('P345', []):
            snak = claim.get('mainsnak') or {}
            value = (snak.get('datavalue') or {}).get('value')
            if isinstance(value, str) and value.startswith('tt') and value not in found:
                found.append(value)
    return found


def fetch_omdb_rating(client, imdb_id, api_key):
    try:
        response = client.get(OMDB_URL, params={'i': imdb_id, 'apikey': api_key})
    except httpx.HTTPError:
        return None
    if response.status_code != 200:
        return None
    return to_float(response.json().get('imdbRating'))


def patch_page(client, page_id, payload, title):
    global fail_logged
    response = client.patch('/pages/' + page_id, json={'properties': payload})
    time.sleep(NOTION_GAP)
    if response.status_code < 400:
        return True
    if fail_logged < FAIL_LOG_LIMIT:
        fail_logged += 1
        log('patch failed {0} {1} {2}'.format(title, response.status_code, response.text[:300]))
    if len(payload) < 2:
        return False
    succeeded = False
    for name in list(payload):
        single = client.patch('/pages/' + page_id, json={'properties': {name: payload[name]}})
        time.sleep(NOTION_GAP)
        if single.status_code < 400:
            succeeded = True
        elif fail_logged < FAIL_LOG_LIMIT:
            fail_logged += 1
            log('single patch failed {0} {1} {2}'.format(name, single.status_code, single.text[:300]))
    return succeeded


def sync_notion(entries):
    token = os.environ.get('NOTION_TOKEN', '').strip()
    data_source_id = os.environ.get('NOTION_DATA_SOURCE_ID', '').strip()
    omdb_key = os.environ.get('OMDB_API_KEY', '').strip()
    if not token or not data_source_id:
        log('notion keys missing, skipping notion sync')
        return None

    by_id = {entry['imdbId']: entry for entry in entries}
    by_title = unique_title_index(entries)
    log('title index size {0}'.format(len(by_title)))

    report = {
        'rows': 0,
        'matchedById': 0,
        'matchedByTitle': 0,
        'matchedByWikidata': 0,
        'updated': 0,
        'unmatchedRows': [],
        'outsideChartRows': [],
        'chartMissingKoTitle': [
            {'rank': entry['rank'], 'title': entry.get('title')}
            for entry in entries if not entry.get('titleKo')
        ],
        'duplicateTitleKeys': duplicate_keys(entries),
        'chartEntriesNotMatched': [],
    }

    matched_ids = set()
    resolved = {}
    wd_calls = 0
    omdb_calls = 0
    updated = 0

    with notion_client(token) as client:
        schema = load_schema(client, data_source_id)
        log('schema properties {0}'.format(len(schema)))
        for name in sorted(schema):
            definition = schema[name] if isinstance(schema[name], dict) else {}
            log('  property {0} type {1}'.format(name, definition.get('type')))

        title_prop = pick_property(schema, ('title',), ())
        rank_prop = pick_property(schema, ('number',), ('imdb', TOKEN_RANK))
        rating_prop = pick_property(schema, ('number',), ('imdb', TOKEN_RATING))
        imdb_prop = pick_property(schema, ('rich_text', 'url'), ('imdb', 'id'))
        log('tokens {0} {1}'.format(TOKEN_RANK, TOKEN_RATING))
        log('detected title {0} rank {1} rating {2} imdbId {3}'.format(title_prop, rank_prop, rating_prop, imdb_prop))
        report['properties'] = {
            'title': title_prop,
            'rank': rank_prop,
            'rating': rating_prop,
            'imdbId': imdb_prop,
        }

        if rank_prop is None and rating_prop is None:
            log('no number property matched the imdb tokens, check the property list above')
            return report

        rows = query_rows(client, data_source_id)
        report['rows'] = len(rows)
        log('notion rows {0}'.format(len(rows)))

        with httpx.Client(timeout=20.0) as omdb, httpx.Client(headers=WD_API_HEADERS, timeout=30.0, follow_redirects=True) as wd:
            for index, row in enumerate(rows, start=1):
                props = row.get('properties', {})
                page_id = row.get('id')
                title = plain_text(props.get(title_prop)) if title_prop else ''
                raw_id = plain_text(props.get(imdb_prop)) if imdb_prop else ''
                imdb_id = imdb_id_from_url(raw_id) or ''
                outside = False

                entry = by_id.get(imdb_id) if imdb_id else None
                if entry is not None:
                    report['matchedById'] += 1
                if entry is None and title:
                    for key in row_title_keys(title):
                        entry = by_title.get(key)
                        if entry is not None:
                            report['matchedByTitle'] += 1
                            imdb_id = entry['imdbId']
                            break
                if entry is None and title and wd_calls < WD_MAX_LOOKUPS:
                    found = resolved.get(title)
                    if found is None:
                        found = wikidata_lookup(wd, title)
                        resolved[title] = found
                        wd_calls += 1
                        time.sleep(WD_GAP)
                    for candidate in found:
                        if candidate in by_id:
                            entry = by_id[candidate]
                            imdb_id = candidate
                            report['matchedByWikidata'] += 1
                            break
                    if entry is None and found:
                        outside = True
                        if not imdb_id:
                            imdb_id = found[0]
                        report['outsideChartRows'].append({'title': title, 'imdbId': found[0]})
                if entry is not None:
                    matched_ids.add(entry['imdbId'])
                elif title and not outside:
                    report['unmatchedRows'].append(title)

                payload = {}
                if rank_prop:
                    desired_rank = entry['rank'] if entry else None
                    if number_value(props.get(rank_prop)) != desired_rank:
                        payload[rank_prop] = {'number': desired_rank}
                if rating_prop:
                    desired_rating = entry.get('rating') if entry else None
                    if desired_rating is None and imdb_id and omdb_key and omdb_calls < OMDB_MAX_CALLS:
                        desired_rating = fetch_omdb_rating(omdb, imdb_id, omdb_key)
                        omdb_calls += 1
                        time.sleep(OMDB_GAP)
                    if desired_rating is not None and number_value(props.get(rating_prop)) != desired_rating:
                        payload[rating_prop] = {'number': desired_rating}
                if imdb_prop and imdb_id and not raw_id:
                    if schema.get(imdb_prop, {}).get('type') == 'rich_text':
                        payload[imdb_prop] = {'rich_text': [{'type': 'text', 'text': {'content': imdb_id}}]}

                if payload and patch_page(client, page_id, payload, title):
                    updated += 1

                if index % 50 == 0:
                    log('progress {0}/{1} updated {2}'.format(index, len(rows), updated))

    report['updated'] = updated
    report['wikidataLookups'] = wd_calls
    report['omdbCalls'] = omdb_calls
    report['chartEntriesNotMatched'] = [
        {'rank': entry['rank'], 'title': entry.get('title'), 'titleKo': entry.get('titleKo')}
        for entry in entries if entry['imdbId'] not in matched_ids
    ]

    log('matched by id {0}, by title {1}, by wikidata {2}'.format(
        report['matchedById'], report['matchedByTitle'], report['matchedByWikidata']))
    log('unmatched rows {0}, rows outside the chart {1}'.format(
        len(report['unmatchedRows']), len(report['outsideChartRows'])))
    if report['unmatchedRows']:
        log('unmatched sample ' + ' / '.join(report['unmatchedRows'][:12]))
    log('chart entries with no notion row {0}'.format(len(report['chartEntriesNotMatched'])))
    log('notion updated {0}, omdb calls {1}, wikidata lookups {2}'.format(updated, omdb_calls, wd_calls))
    return report


def write_report(report):
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    REPORT_PATH.write_text(payload, encoding='utf-8')
    log('sync-report.json written')


def commit_report():
    if not os.environ.get('GITHUB_ACTIONS'):
        return
    commands = [
        ['git', 'add', '-f', str(REPORT_PATH)],
        ['git', '-c', 'user.name=github-actions[bot]',
         '-c', 'user.email=41898282+github-actions[bot]@users.noreply.github.com',
         'commit', '-m', 'chore: sync report'],
        ['git', 'push'],
    ]
    for command in commands:
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            log('git step failed {0} {1}'.format(' '.join(command[:2]), (result.stderr or result.stdout)[:200]))
            return
    log('sync-report.json pushed')


def main():
    entries = collect_chart()
    labels, alts = fetch_ko_titles(entries)
    for entry in entries:
        label = labels.get(entry['imdbId'])
        if label:
            entry['titleKo'] = label
        bucket = alts.get(entry['imdbId'])
        if bucket:
            entry['_koAlts'] = bucket
    write_cache(entries)
    try:
        report = sync_notion(entries)
    except httpx.HTTPStatusError as error:
        log('notion request failed {0} {1}'.format(error.response.status_code, error.response.text[:300]))
        return 1
    if report:
        write_report(report)
        commit_report()
    return 0


if __name__ == '__main__':
    sys.exit(main())
