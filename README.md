# 📰 RSS 뉴스 파이프라인

> **최근 변경 사항**
>
> * RSS 소스를 `rss_sources.yaml` 로 관리
> * 모든 수집 결과를 `raw_feeds/` 폴더에 JSON 형식으로 저장
> * 네이버 검색 API 연동 및 광고 제거 기능 강화
> * `deduplicate_fuzzy()` 함수로 비슷한 제목의 기사까지 자동 제거
> * `.env` 파일이 있으면 `python-dotenv` 로 자동 로드
> * `process_blocks()` 함수로 여러 텍스트 블록을 간단히 요약·번역 가능
>
> ⚠️ `feedparser` 가 설치되지 않으면 `main.py` 가 동작하지 않습니다.

---

## 프로젝트 개요

본 프로젝트는 다양한 RSS 피드를 수집·가공하여 **깨끗한 뉴스 요약 리스트**를 생성하는 Python 파이프라인입니다. 🤖 ➜ 📰 ➜ ✨

1. **수집(Collect)** – RSS·API 등에서 최근 24시간 기사만 가져오기
2. **중복 제거(Deduplicate)** – 동일한 링크나 제목을 가진 기사 삭제
3. **정제(Clean)** – 광고·불필요 태그 제거, 공백(normalize whitespace) 통일
4. **요약(Summarize)** – 필요한 경우 LLM·알고리즘으로 핵심만 추출
5. **정렬(Sort)** – 발행일(`pub_date`) 기준 최신순 정렬
6. **출력(Output)** – Markdown/JSON 등 원하는 포맷으로 저장

---

## 디렉토리 구조

```
📦 project_root
 ┣ utubenews/
 ┃ ┣ __init__.py
 ┃ ┣ article_extractor.py
 ┃ ┣ collector.py
 ┃ ┣ naver_news_client.py
 ┃ ┣ pipeline.py
 ┃ ┣ summarizer.py
 ┃ ┣ text_utils.py
 ┃ ┣ block_processor.py
 ┃ ┗ utils.py
 ┣ raw_feeds/             # 결과 JSON 저장 폴더 (파이프라인 실행 시 자동 생성)
 ┣ static/               # 클라이언트용 스크립트
 ┃ ┗ error_logger.js
 ┣ rss_sources.yaml       # 수집 대상 목록
 ┣ main.py                # 엔트리 포인트
 ┣ requirements.txt       # 필요 패키지 목록
 ┗ README.md
```

## rss_sources.yaml 설정

`rss_sources.yaml` 파일은 수집할 RSS 혹은 네이버 검색 소스를 정의합니다.
네이버 검색을 사용할 때는 `max_pages` 값으로 몇 페이지까지 결과를 가져올지
정합니다. 이 값이 지나치게 크면 한 번에 수백 건의 기사가 모일 수 있으니,
RSS 피드와 네이버 검색 간의 균형을 맞추려면 보통 **1–2 페이지** 정도로
설정하는 것을 권장합니다.

```yaml
- type: naver
  name: 네이버 IT 키워드
  query: IT
  topic: IT
  max_pages: 4
```

위와 같이 페이지 수를 크게 잡으면 한 번 실행할 때마다 수백 건의 검색 결과가
모일 수 있습니다.

`max_pages` 를 1로 두면 다음과 같이 수집량을 줄일 수 있습니다.

```yaml
- type: naver
  name: 테스트용
  query: 임시
  topic: IT
  max_pages: 1
```

## 키워드 필터링

`utubenews/collector.py` 의 `_INCLUDE_KEYWORDS` 와 `_EXCLUDE_KEYWORDS` 목록을 수정하면
네이버 검색 결과의 필터링 기준을 조정할 수 있습니다. RSS 피드 기사는 키워드 필터링을
적용하지 않고, 네이버 기사에 대해서만 작동합니다.

```python
_INCLUDE_KEYWORDS = ["프로그램", "사이버 보안"]
_EXCLUDE_KEYWORDS = [
    "공항",
    "cctv",
    "경비",
    "정치",
    "교육 프로그램",
    "대학일자리",
    "양성",
]
```

필요에 따라 위 목록을 원하는 단어로 바꾸고 파이프라인을 실행하세요.

---

## 중복 기사 제거

`deduplicate_fuzzy()` 함수는 링크가 같은 기사뿐 아니라 제목이나 내용이
비슷한 기사도 찾아서 제거합니다. 기본 임계값은 `0.9`로, 값이 낮을수록
더 엄격하게 중복을 인식합니다. 파이프라인은 내부적으로
`deduplicate_fuzzy(arts, similarity_threshold=0.9)` 형태로 호출하므로
필요하다면 이 값을 조정해 중복 판정 기준을 바꿀 수 있습니다.

---

## 요구 사항

| 항목             | 최소 버전  |
| -------------- | ------ |
| Python         | 3.8 이상 |
| feedparser     | 6.0+   |
| requests       | 2.0+   |
| beautifulsoup4 | 4.0+   |

> **TIP:** 추가 패키지가 필요할 경우 `requirements.txt` 에 기재하세요.

---

## 설치

```bash
# 저장소 클론
$ git clone <repo_url>
$ cd <repo_root>

# 의존성 설치
$ pip install -r requirements.txt  # deep_translator>=1.11 포함
# 환경 파일 준비
$ cp .env.sample .env
```
`.env` 파일의 `NAVER_CLIENT_ID` 와 `NAVER_CLIENT_SECRET` 값을 자신의
네이버 API 자격 증명으로 채워 넣으세요.
`.env`에는 이 두 항목만 있으면 됩니다.
`python-dotenv` 패키지가 설치되어 있으면 프로그램 실행 시 `.env` 파일을 자동으로 로드합니다.
> `feedparser` 가 설치되어 있지 않으면 `main.py` 실행 시 `ModuleNotFoundError` 가 발생합니다.

---

## 사용 방법

```bash
# 기본 파이프라인 실행 (최근 1일 기사 수집)
$ python main.py
# 예: 최근 3일간의 기사를 모으려면
$ python main.py --days 3
# 네이버 기사 수를 조절하려면 (기본값 10)
$ python main.py --max-naver 10
# 전체 기사 수 상한을 두려면 (기본값 30)
$ python main.py --max-total 30
# 기사 페이지를 캡처하려면
$ python main.py --with-screenshot
# 두 옵션을 함께 쓰면 네이버 기사 "max-naver" 만큼을 우선 확보하고
# 나머지는 "max-total - max-naver" 범위에서 다른 소스 기사로 채워집니다.
# 실행하면 제목과 링크만 담은 `articles_*.json` 파일이 `raw_feeds/` 폴더에 생성됩니다.
# 폴더가 미리 없더라도 파이프라인이 처음 실행될 때 자동으로 만들어집니다.
# 진행 상황을 보려면 `--log-level INFO` 나 `LOG_LEVEL=INFO` 환경 변수를 지정하세요.

# 결과 파일 예시
raw_feeds/
 ┗ articles_20250613_131459.json
```

`pipeline.py`의 각 단계는 `collect_articles()`, `deduplicate()`, `sort_articles()`,
`save_articles()` 함수로 나뉘어 있습니다. 본문 추출과 요약이 필요하다면
`enrich_articles()` 함수를 별도로 호출하여 처리할 수 있습니다.

### 텍스트 블록 처리

뉴스 기사 외의 짧은 글 목록을 한꺼번에 요약하고 번역하려면
`utubenews.process_blocks()` 함수를 사용할 수 있습니다. 리스트 형태의
원본 블록과(선택적으로) 제목 리스트를 넘기면 요약된 스크립트를 반환하며,
`target_lang` 파라미터로 원하는 언어 번역도 가능합니다.

### 브라우저 스크립트 오류 확인

웹 페이지에서 파이프라인 결과를 활용하는 경우 자바스크립트 오류나 경고를
쉽게 확인하려면 `static/error_logger.js` 파일을 HTML에 포함합니다.

```html
<script src="static/error_logger.js"></script>
```

이 스크립트는 전역 `error` 와 `unhandledrejection` 이벤트를 가로채 콘솔에
로그를 남겨 디버깅을 도와줍니다.



## 테스트

```bash
# 문법 검사 (컴파일 에러 여부 확인)
$ python -m py_compile $(git ls-files '*.py')

# 간단한 동작 테스트 실행
$ python -m unittest discover -s tests -v
```

> ✅ 위 명령은 모든 `.py` 파일이 정상 컴파일되는지 확인합니다.

---

## 배포

1. `git tag vX.Y.Z` 로 버전 태그 추가
2. GitHub Release 생성 후 결과물 업로드 (예: `raw_feeds/*.json`)

---

## 문제 해결

| 증상                                | 원인          | 해결 방법                                          |
| --------------------------------- | ----------- | ---------------------------------------------- |
| `ModuleNotFoundError: feedparser` | 의존 패키지 누락   | `pip install feedparser`                       |
| 기사 본문이 비정상적으로 길거나 HTML 태그 포함      | 광고 제거 로직 실패 | `utubenews/article_extractor.py` 의 `clean_text()` 규칙 수정 |
| `HTTPError: 401`                  | 네이버 API 키 누락 또는 잘못됨 | `.env`의 `NAVER_CLIENT_ID`와 `NAVER_CLIENT_SECRET` 값을 설정 |

### 번역 오류 해결

번역 기능은 인터넷 연결을 필요로 하며 `deep_translator` 패키지가 설치되어야 정상 작동합니다. 기본적으로 `requirements.txt` 에 포함되어 있으므로 별도 설치가 필요하지 않습니다.
실행 중 `Translation failed` 경고가 표시되면 네트워크 접근을 확인하고 필요한 경우 다음과 같이 재설치하세요.

```bash
$ pip install deep_translator>=1.11
```

이후 다시 명령을 실행하면 대부분 문제가 해결됩니다.


---

## 기여 방법

1. Issue 또는 Pull Request 생성 전 `CONTRIBUTING.md` 확인
2. 수집 소스 확장 시 `utubenews/collector.py` 수정
3. 코딩 컨벤션: **PEP 8 + Black**

---

## 라이선스

본 프로젝트는 [MIT 라이선스](LICENSE) 하에 배포됩니다. 자세한 내용은
LICENSE 파일을 참고하세요.

