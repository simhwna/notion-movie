#!/usr/bin/env python3
'''IMDb Top 250을 갱신해 data/top250.json에 저장하고 노션 Movies DB의 순위와 평점을 맞춘다.

수집 우선순위
  1. imdb.com/chart/top 의 JSON-LD, __NEXT_DATA__, DOM
  2. top250.info/charts 표. IMDb가 클라우드 아이프를 막을 때 사용한다

환경 변수
  NOTION_TOKEN           노션 내부 통합 토큰
  NOTION_DATA_SOURCE_ID  Movies DB의 data source id
  OMDB_API_KEY           OMDb 키. 없으면 차트에 없는 영화의 평점 조회를 건너뛴다

모든 경로에서 250건을 얻지 못하면 파일을 덮어쓰지 않고 종료 코드 1로 끝낸다.
'''
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

IMDB_CHART_URL = 'https://www.imdb.com/chart/top/'
INFO_CHART_URLS = ('https://top250.info/charts', 'http://top250.info/charts')
OMDB_URL = 'https://www.omdbapi.com/'
OUT_PATH = Path('data/top250.json')
NOTION_API = 'https://api.notion.com/v1'
NOTION_VERSION = '2025-09-03'
NOTION_GAP = 0.4
OMDB_GAP = 0.25
OMDB_MAX_CALLS = 200
EXPECTED = 250

BROWSER_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

PROP_RANK = 'IMDb 순위 숫자'
PROP_RATING = 'IMDb 평점'
PROP_IMDB_ID = 'IMDb ID'
PROP_TITLE = '제목'


def log(message):
    print(message, flush=True)


def fetch_html(url):
    try:
        with httpx.Client(headers=BROWSER_HEADERS, timeout=30.0, follow_redirects=True) as client:
            response = client.get(url)
    except httpx.HTTPError as error:
        log('요청 실패 {0} {1}'.format(url, error))
        return None
    log('요청 {0} 상태 {1} 분량 {2}'.format(url, response.status_code, len(response.text)))
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
        entries = dedupe(parser(soup))
        log('IMDb {0} 파싱 결과 {1}건'.format(name, len(entries)))
        if name == 'DOM' and len(entries) > EXPECTED:
            entries = dedupe(entries[:EXPECTED])
            log('DOM 결과를 상위 250건으로 자른다')
        if len(entries) == EXPECTED:
            return entries
    return []


def collect_from_info():
    for url in INFO_CHART_URLS:
        html = fetch_html(url)
        if not html:
            continue
        entries = dedupe(parse_top250_info(html))
        log('top250.info 파싱 결과 {0}건'.format(len(entries)))
        if len(entries) == EXPECTED:
            return entries
    return []


def collect_chart():
    entries = collect_from_imdb()
    if entries:
        log('IMDb 원본에서 250건 확보')
        return entries
    log('IMDb 원본 실패. 폴백 소스로 전환한다')
    entries = collect_from_info()
    if entries:
        log('top250.info에서 250건 확보')
        return entries
    raise SystemExit('250건을 얻지 못했다. 파일을 덮어쓰지 않고 종료한다')


def write_cache(entries):
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(entries, ensure_ascii=False, indent=2) + '\n'
    if OUT_PATH.exists() and OUT_PATH.read_text(encoding='utf-8') == payload:
        log('top250.json 변경 없음')
        return False
    OUT_PATH.write_text(payload, encoding='utf-8')
    log('top250.json 갱신 {0}건'.format(len(entries)))
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
    parts = prop.get('rich_text') or prop.get('title') or []
    return ''.join(part.get('plain_text', '') for part in parts).strip()


def number_value(prop):
    return prop.get('number') if isinstance(prop, dict) else None


def normalize_title(value):
    return re.sub(r'[^0-9a-z가-힣]+', '', (value or '').lower())


def unique_title_index(entries):
    counts = {}
    for entry in entries:
        key = normalize_title(entry.get('title'))
        if key:
            counts[key] = counts.get(key, 0) + 1
    index = {}
    for entry in entries:
        key = normalize_title(entry.get('title'))
        if key and counts.get(key) == 1:
            index[key] = entry
    return index


def fetch_omdb_rating(client, imdb_id, api_key):
    try:
        response = client.get(OMDB_URL, params={'i': imdb_id, 'apikey': api_key})
    except httpx.HTTPError:
        return None
    if response.status_code != 200:
        return None
    return to_float(response.json().get('imdbRating'))


def sync_notion(entries):
    token = os.environ.get('NOTION_TOKEN', '').strip()
    data_source_id = os.environ.get('NOTION_DATA_SOURCE_ID', '').strip()
    omdb_key = os.environ.get('OMDB_API_KEY', '').strip()
    if not token or not data_source_id:
        log('노션 키가 없어 노션 갱신을 건너뛴다')
        return

    by_id = {entry['imdbId']: entry for entry in entries}
    by_title = unique_title_index(entries)
    updated = 0
    omdb_calls = 0

    with notion_client(token) as client:
        schema = load_schema(client, data_source_id)
        has_rank = PROP_RANK in schema
        has_rating = PROP_RATING in schema
        if not has_rank and not has_rating:
            log('갱신할 속성이 스키마에 없다')
            return
        rows = query_rows(client, data_source_id)
        log('노션 행 {0}건 조회'.format(len(rows)))

        with httpx.Client(timeout=20.0) as omdb:
            for row in rows:
                props = row.get('properties', {})
                page_id = row.get('id')
                imdb_id = plain_text(props.get(PROP_IMDB_ID))
                title = plain_text(props.get(PROP_TITLE))
                entry = by_id.get(imdb_id) if imdb_id else None
                if entry is None and title:
                    entry = by_title.get(normalize_title(title))

                payload = {}
                if has_rank:
                    desired_rank = entry['rank'] if entry else None
                    if number_value(props.get(PROP_RANK)) != desired_rank:
                        payload[PROP_RANK] = {'number': desired_rank}
                if has_rating:
                    desired_rating = entry.get('rating') if entry else None
                    if desired_rating is None and imdb_id and omdb_key and omdb_calls < OMDB_MAX_CALLS:
                        desired_rating = fetch_omdb_rating(omdb, imdb_id, omdb_key)
                        omdb_calls += 1
                        time.sleep(OMDB_GAP)
                    if desired_rating is not None and number_value(props.get(PROP_RATING)) != desired_rating:
                        payload[PROP_RATING] = {'number': desired_rating}
                if not payload:
                    continue

                response = client.patch('/pages/' + page_id, json={'properties': payload})
                time.sleep(NOTION_GAP)
                if response.status_code >= 400:
                    log('갱신 실패 {0} {1} {2}'.format(title, response.status_code, response.text[:200]))
                    continue
                updated += 1

    log('노션 {0}건 갱신, OMDb 호출 {1}회'.format(updated, omdb_calls))


def main():
    entries = collect_chart()
    write_cache(entries)
    try:
        sync_notion(entries)
    except httpx.HTTPStatusError as error:
        log('노션 요청 실패 {0} {1}'.format(error.response.status_code, error.response.text[:200]))
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
