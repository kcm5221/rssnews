# 📰 RSS 뉴스 파이프라인

> **최근 변경 사항**
>
> * RSS 소스를 `rss_sources.yaml` 로 관리
> * 모든 수집 결과를 `raw_feeds/` 폴더에 JSON 형식으로 저장
> * 네이버 검색 API 연동 및 광고 제거 기능 강화
>
> ⚠️ `feedparser` 가 설치되지 않으면 `main.py` 가 동작하지 않습니다.

---

## 프로젝트 개요

본 프로젝트는 다양한 RSS 피드를 수집·가공하여 **깨끗한 뉴스 요약 리스트**를 생성하는 Python 파이프라인입니다. 🤖 ➜ 📰 ➜ ✨

1. **수집(Collect)** – RSS·API 등에서 최근 24시간 기사만 가져오기
2. **정제(Clean)** – 광고·불필요 태그 제거, 공백(normalize whitespace) 통일
3. **요약(Summarize)** – 필요한 경우 LLM·알고리즘으로 핵심만 추출
4. **정렬(Sort)** – 발행일(`pub_date`) 기준 최신순 정렬
5. **출력(Output)** – Markdown/JSON 등 원하는 포맷으로 저장

---

## 디렉토리 구조

```
📦 project_root
 ┣ utubenews/
 ┃ ┣ __init__.py
 ┃ ┣ article_extractor.py
 ┃ ┣ collector.py
 ┃ ┣ naver_client.py
 ┃ ┣ naver_news_client.py
 ┃ ┣ pipeline.py
 ┃ ┣ summarizer.py
 ┃ ┣ text_utils.py
 ┃ ┗ utils.py
 ┣ raw_feeds/             # 결과 JSON 저장 폴더
 ┣ static/               # 클라이언트용 스크립트
 ┃ ┗ error_logger.js
 ┣ rss_sources.yaml       # 수집 대상 목록
 ┣ main.py                # 엔트리 포인트
 ┣ requirements.txt       # 필요 패키지 목록
 ┗ README.md
```

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
$ pip install -r requirements.txt
```

> `feedparser` 가 설치되어 있지 않으면 `main.py` 실행 시 `ModuleNotFoundError` 가 발생합니다.

---

## 사용 방법

```bash
# 기본 파이프라인 실행
$ python main.py

# 결과 파일 예시
raw_feeds/
 ┗ articles_20250613_131459.json
```

`pipeline.py`의 각 단계는 `collect_articles()`, `enrich_articles()`,
`sort_articles()`, `save_articles()` 함수로 나뉘어 있어 원하는 단계만 독립적으로
호출할 수 있습니다.

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

---

## 기여 방법

1. Issue 또는 Pull Request 생성 전 `CONTRIBUTING.md` 확인
2. 수집 소스 확장 시 `utubenews/collector.py` 수정
3. 코딩 컨벤션: **PEP 8 + Black**

---

## 라이선스

이 프로젝트의 저작권은 본인(© KCM)에게 있습니다.
