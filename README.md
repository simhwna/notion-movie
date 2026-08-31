# Notion Movie

안드로이드 앱에서 영화를 검색해 별점과 관람일을 기록하면 노션 Movies DB 에 자동으로 쌓이는 개인용 앱이다.
저장소 하나로 앱 소스와 IMDb Top 250 자동 갱신을 함께 관리한다.

## 구성

- `app` 안드로이드 앱. Kotlin, Jetpack Compose, 단일 모듈, minSdk 26
- `scripts/refresh_top250.py` IMDb Top 250 수집과 노션 순위·평점 일괄 갱신
- `.github/workflows/refresh-imdb-top250.yml` 매주 월요일 새벽 4시 자동 실행
- `data/top250.json` 순위 캐시. 앱이 아래 주소로 직접 읽는다

```
https://raw.githubusercontent.com/simhwna/notion-movie/main/data/top250.json
```

## 안드로이드 스튜디오에서 열기

1. 이 저장소를 내려받는다. 상단 Code 버튼의 Download ZIP 을 쓰거나 원하는 방법을 쓴다
2. 안드로이드 스튜디오에서 Open 을 누르고 압축을 푼 폴더를 고른다
3. `local.properties.sample` 을 같은 위치에 `local.properties` 로 복사한다
4. 노션 계획 페이지 섹션 0 의 보안 블록 값을 `local.properties` 에 채운다. `sdk.dir` 은 스튜디오가 자동으로 채운다
5. Gradle 동기화가 끝나면 실행 버튼을 누른다

키가 비어 있어도 앱은 실행된다. 값이 없는 기능만 설정 탭에서 미설정으로 표시된다.

## 키가 하는 일

| 키 | 쓰임 |
| --- | --- |
| TMDB_TOKEN | 영화 검색, 한국어 제목, 장르, 감독, 포스터 |
| OMDB_API_KEY | IMDb 평점 |
| NOTION_TOKEN | Movies DB 읽기와 쓰기 |
| NOTION_DATA_SOURCE_ID | 대상 데이터 소스 |
| KOBIS_API_KEY | 감독 한글 이름 보강 |
| KMDB_API_KEY | 감독 한글 이름 보강 예비 |

`local.properties` 는 절대 커밋하지 않는다. 커밋 제외 목록에 이미 들어 있다.
