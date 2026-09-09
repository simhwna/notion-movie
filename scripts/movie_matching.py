"""IMDb ID를 우선하는 노션 영화 판별과 순위 갱신."""
from __future__ import annotations

from dataclasses import dataclass
import os
import re
from urllib.parse import urlsplit


@dataclass(frozen=True)
class Match:
    imdb_id: str | None
    entry: dict | None
    method: str
    status: str


def normalize_imdb_id(value):
    """ID 자체 또는 IMDb 영화 URL만 허용한다."""
    if not isinstance(value, str):
        return None
    raw = value.strip()
    if re.fullmatch(r'tt[0-9]{7,}', raw, re.IGNORECASE):
        return raw.lower()
    if raw.lower().startswith(('imdb.com/', 'www.imdb.com/', 'm.imdb.com/')):
        raw = 'https://' + raw
    try:
        parsed = urlsplit(raw)
    except ValueError:
        return None
    if parsed.scheme or parsed.netloc:
        host = (parsed.hostname or '').lower()
        if parsed.scheme.lower() not in ('https', 'http'):
            return None
        if host != 'imdb.com' and not host.endswith('.imdb.com'):
            return None
        if parsed.username or parsed.password:
            return None
    elif not raw.startswith('/title/'):
        return None
    match = re.fullmatch(r'/title/(tt[0-9]{7,})(?:/.*)?', parsed.path, re.IGNORECASE)
    return match.group(1).lower() if match else None


def property_text(prop):
    if not isinstance(prop, dict):
        return ''
    if isinstance(prop.get('url'), str):
        return prop['url'].strip()
    parts = prop.get('rich_text') or prop.get('title') or []
    return ''.join(
        part.get('plain_text') or (part.get('text') or {}).get('content', '')
        for part in parts if isinstance(part, dict)
    ).strip()


def title_key(value):
    return re.sub(r'[^0-9a-z가-힣]+', '', (value or '').lower())


def title_keys(entry):
    values = [entry.get('title'), entry.get('titleKo')]
    values.extend(entry.get('_koAlts') or [])
    return {title_key(value) for value in values if title_key(value)}


def row_title_keys(title):
    base = (title or '').strip()
    trimmed = re.sub(r'\s*[\(\[]?\d{4}[\)\]]?\s*$', '', base)
    return {title_key(value) for value in (base, trimmed) if title_key(value)}


def chart_index(entries, expected=250):
    """불완전한 차트에서 순위 밖 여부를 판정하지 않는다."""
    if len(entries) != expected:
        raise ValueError('incomplete IMDb chart')
    by_id = {}
    ranks = set()
    for original in entries:
        imdb_id = normalize_imdb_id(original.get('imdbId'))
        rank = original.get('rank')
        if not imdb_id or imdb_id in by_id:
            raise ValueError('invalid or duplicate IMDb ID in chart')
        if type(rank) is not int or not 1 <= rank <= expected or rank in ranks:
            raise ValueError('invalid or duplicate rank in chart')
        if not isinstance(original.get('title'), str) or not original['title'].strip():
            raise ValueError('missing chart title')
        ranks.add(rank)
        by_id[imdb_id] = dict(original, imdbId=imdb_id)
    return by_id


def title_index(by_id):
    index = {}
    for imdb_id, entry in by_id.items():
        for key in title_keys(entry):
            index.setdefault(key, set()).add(imdb_id)
    return index


def resolve_movie(raw_id, title, by_id, by_title, lookup):
    """입력된 ID는 제목이나 위키데이터 후보로 대체하지 않는다."""
    if raw_id and raw_id.strip():
        imdb_id = normalize_imdb_id(raw_id)
        if not imdb_id:
            return Match(None, None, 'id', 'invalid_id')
        entry = by_id.get(imdb_id)
        return Match(imdb_id, entry, 'id', 'matched' if entry else 'outside_chart')

    candidates = set()
    for key in row_title_keys(title):
        candidates.update(by_title.get(key, set()))
    if len(candidates) > 1:
        return Match(None, None, 'title', 'ambiguous')
    if candidates:
        imdb_id = next(iter(candidates))
        return Match(imdb_id, by_id[imdb_id], 'title', 'matched')
    if not title or not title.strip():
        return Match(None, None, 'none', 'unresolved')

    candidates = {normalized for value in lookup(title)
                  if (normalized := normalize_imdb_id(value))}
    if len(candidates) > 1:
        return Match(None, None, 'wikidata', 'ambiguous')
    if not candidates:
        return Match(None, None, 'wikidata', 'unresolved')
    imdb_id = next(iter(candidates))
    entry = by_id.get(imdb_id)
    return Match(imdb_id, entry, 'wikidata', 'matched' if entry else 'outside_chart')


def imdb_property(schema):
    aliases = ('imdbid', 'imdblink', 'imdburl', 'imdb링크', 'imdb')
    for alias in aliases:
        matches = [name for name, spec in schema.items()
                   if isinstance(spec, dict) and spec.get('type') in ('rich_text', 'url')
                   and title_key(name) == alias]
        if matches:
            return matches[0]
    return None


def update_payload(match, props, schema, names, raw_id, omdb_rating):
    if match.status not in ('matched', 'outside_chart'):
        return {}
    payload = {}
    rank_prop, rating_prop, id_prop = names
    if rank_prop:
        desired_rank = match.entry['rank'] if match.entry else None
        current = (props.get(rank_prop) or {}).get('number')
        if current != desired_rank:
            payload[rank_prop] = {'number': desired_rank}
    if rating_prop:
        rating = match.entry.get('rating') if match.entry else None
        if rating is None and match.imdb_id:
            rating = omdb_rating(match.imdb_id)
        if isinstance(rating, (int, float)) and not isinstance(rating, bool) and 0 <= rating <= 10:
            if (props.get(rating_prop) or {}).get('number') != rating:
                payload[rating_prop] = {'number': rating}
    if id_prop and match.imdb_id and not raw_id:
        if schema[id_prop]['type'] == 'rich_text':
            payload[id_prop] = {'rich_text': [{'type': 'text', 'text': {'content': match.imdb_id}}]}
        elif schema[id_prop]['type'] == 'url':
            payload[id_prop] = {'url': 'https://www.imdb.com/title/' + match.imdb_id + '/'}
    return payload


def sync_notion(entries, api):
    """기존 수집·통신 함수를 재사용하고 판별과 저장 대상을 제한한다."""
    by_id = chart_index(entries, api.EXPECTED)
    by_title = title_index(by_id)
    token = os.environ.get('NOTION_TOKEN', '').strip()
    data_source_id = os.environ.get('NOTION_DATA_SOURCE_ID', '').strip()
    omdb_key = os.environ.get('OMDB_API_KEY', '').strip()
    if not token or not data_source_id:
        api.log('notion keys missing, skipping notion sync')
        return None
    report = dict(rows=0, matchedById=0, matchedByTitle=0, matchedByWikidata=0,
                  outsideChart=0, invalidId=0, ambiguous=0, unresolved=0,
                  updated=0, updateFailed=0, wikidataLookups=0, omdbCalls=0)
    resolved = {}
    with api.notion_client(token) as client:
        schema = api.load_schema(client, data_source_id)
        title_prop = api.pick_property(schema, ('title',), ())
        rank_prop = api.pick_property(schema, ('number',), ('imdb', '순위'))
        rating_prop = api.pick_property(schema, ('number',), ('imdb', '평점'))
        id_prop = imdb_property(schema)
        if not rank_prop and not rating_prop and not id_prop:
            api.log('no supported IMDb properties')
            return report
        rows = api.query_rows(client, data_source_id)
        report['rows'] = len(rows)
        with api.httpx.Client(timeout=20.0) as omdb, api.httpx.Client(
            headers=api.WD_API_HEADERS, timeout=30.0, follow_redirects=True
        ) as wd:
            def lookup(title):
                if title in resolved:
                    return resolved[title]
                if report['wikidataLookups'] >= api.WD_MAX_LOOKUPS:
                    return []
                found = api.wikidata_lookup(wd, title)
                resolved[title] = found
                report['wikidataLookups'] += 1
                api.time.sleep(api.WD_GAP)
                return found

            def rating(imdb_id):
                if not omdb_key or report['omdbCalls'] >= api.OMDB_MAX_CALLS:
                    return None
                report['omdbCalls'] += 1
                try:
                    return api.fetch_omdb_rating(omdb, imdb_id, omdb_key)
                except ValueError:
                    return None
                finally:
                    api.time.sleep(api.OMDB_GAP)

            for row in rows:
                props = row.get('properties') or {}
                raw_id = property_text(props.get(id_prop)) if id_prop else ''
                title = property_text(props.get(title_prop)) if title_prop else ''
                match = resolve_movie(raw_id, title, by_id, by_title, lookup)
                if match.status == 'matched':
                    report[{'id': 'matchedById', 'title': 'matchedByTitle',
                            'wikidata': 'matchedByWikidata'}[match.method]] += 1
                elif match.status == 'outside_chart':
                    report['outsideChart'] += 1
                else:
                    report[{'invalid_id': 'invalidId', 'ambiguous': 'ambiguous',
                            'unresolved': 'unresolved'}[match.status]] += 1
                payload = update_payload(match, props, schema,
                                         (rank_prop, rating_prop, id_prop), raw_id, rating)
                if payload:
                    # 집계 보고서에는 노션 행 제목이나 ID를 추가하지 않는다.
                    if api.patch_page(client, row['id'], payload, 'movie row'):
                        report['updated'] += 1
                    else:
                        report['updateFailed'] += 1
    api.log('movie matching summary ' + str(report))
    return report
