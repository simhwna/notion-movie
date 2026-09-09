#!/usr/bin/env python3
"""IMDb ID 우선 판별을 사용하는 순위 갱신 실행 파일."""
import sys
import refresh_top250 as source
from movie_matching import chart_index, sync_notion


def main():
    entries = sorted(chart_index(source.collect_chart(), source.EXPECTED).values(),
                     key=lambda entry: entry['rank'])
    labels, alts = source.fetch_ko_titles(entries)
    for entry in entries:
        if labels.get(entry['imdbId']):
            entry['titleKo'] = labels[entry['imdbId']]
        if alts.get(entry['imdbId']):
            entry['_koAlts'] = alts[entry['imdbId']]
    source.write_cache(entries)
    try:
        report = sync_notion(entries, source)
    except source.httpx.HTTPError:
        source.log('notion request failed; cache and existing row values retained where not updated')
        return 1
    if report is not None:
        source.write_report(report)
        source.commit_report()
        if report.get('updateFailed'):
            return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
