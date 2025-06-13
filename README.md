# 📰 RSS 뉴스 파이프라인

> **최근 변경 사항**
>
> * 광고 제거 및 공백(normalization) 기능 추가 → 더 깨끗한 원문 확보
> * 모든 *collector* 가 최근 24시간 기사만 수집하도록 제한 (Naver 클라이언트 포함)
> * 요약 전 텍스트 정제 후 `pub_date` 기준으로 정렬
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
 ┣ 📂collectors        # 사이트별 RSS/HTML 크롤러
 ┣ 📂processors        # 정제·요약 로직
 ┣ 📂utils             # 공통 유틸리티 함수
 ┣ main.py             # 전체 파이프라인 엔트리 포인트
 ┣ requirements.txt    # 필요 패키지 목록
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

# 결과 예시
results/
 ┣ 2025-06-13_summary.json
 ┗ 2025-06-13_summary.md
```

### 커스텀 옵션

| 옵션             | 설명           | 예시         |
| -------------- | ------------ | ---------- |
| `--hours 48`   | 수집 범위(시간) 지정 | 최근 48시간 기사 |
| `--format csv` | 출력 포맷 선택     | CSV 파일 생성  |

---

## 테스트

```bash
# 문법 검사 (컴파일 에러 여부 확인)
$ python -m py_compile $(git ls-files '*.py')
```

> ✅ 위 명령은 모든 `.py` 파일이 정상 컴파일되는지 확인합니다.

---

## 배포

1. `git tag vX.Y.Z` 로 버전 태그 추가
2. GitHub Release 생성 후 결과물 업로드 (예: `results/*.md`)

---

## 문제 해결

| 증상                                | 원인          | 해결 방법                                          |
| --------------------------------- | ----------- | ---------------------------------------------- |
| `ModuleNotFoundError: feedparser` | 의존 패키지 누락   | `pip install feedparser`                       |
| 기사 본문이 비정상적으로 길거나 HTML 태그 포함      | 광고 제거 로직 실패 | `processors/cleaner.py` 의 `remove_ads()` 규칙 추가 |

---

## 기여 방법

1. Issue 또는 Pull Request 생성 전 `CONTRIBUTING.md` 확인
2. 새로운 Collector 추가 시 `collectors/base.py` 상속
3. 코딩 컨벤션: **PEP 8 + Black**

---

## 라이선스

이 프로젝트의 저작권은 본인(© KCM)에게 있습니다.
