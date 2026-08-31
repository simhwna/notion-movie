# notion-movie

안드로이드 앱 Notion Movie 의 저장소. 영화 검색과 별점, 관람일 기록을 노션 Movies DB 로 동기화한다.

## 구성

- `app/` 안드로이드 앱 소스. Kotlin, Jetpack Compose, 단일 모듈, minSdk 26
- `scripts/refresh_top250.py` IMDb Top 250 파싱과 노션 순위·평점 갱신
- `.github/workflows/refresh-imdb-top250.yml` 매주 월요일 새벽 4시 자동 실행, 수동 실행 가능
- `data/top250.json` 순위 캐시. 앱이 raw 주소로 내려받는다

## GitHub Actions 시크릿

Settings → Secrets and variables → Actions 에서 아래 세 개를 등록한다. 값은 저장소에 커밋하지 않는다.

| 이름 | 용도 |
| --- | --- |
| `NOTION_TOKEN` | 노션 내부 통합 토큰 |
| `NOTION_DATA_SOURCE_ID` | Movies DB 의 data source id |
| `OMDB_API_KEY` | OMDb 평점 조회 키 |

## 로컬 개발

`local.properties` 에 아래 여섯 줄을 넣는다. 이 파일은 `.gitignore` 로 제외되어 있다.

```
TMDB_TOKEN=
OMDB_API_KEY=
NOTION_TOKEN=
NOTION_DATA_SOURCE_ID=
KOBIS_API_KEY=
KMDB_API_KEY=
```

## 순위 캐시 주소

```
https://raw.githubusercontent.com/simhwna/notion-movie/main/data/top250.json
```

비공개 저장소의 raw 주소는 인증 없이 열리지 않는다. 앱이 순위를 내려받으려면 이 저장소를 공개로 바꾸거나, `data/top250.json` 만 별도 공개 저장소로 분리한다.

## 수동 실행

Actions 탭에서 refresh-imdb-top250 워크플로를 선택하고 Run workflow 를 누른다. 파싱 결과가 250건이 아니면 파일을 덮어쓰지 않고 실패로 끝난다.
