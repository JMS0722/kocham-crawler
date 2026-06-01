# EuroCham 디렉토리 사이트 분석 보고서

분석일: 2026-06-01

## 1. 사이트 기본 정보

| 항목 | 내용 |
|------|------|
| 사이트 | European Chamber of Commerce in Vietnam (EuroCham) |
| URL | https://eurochamvn.glueup.com |
| 플랫폼 | Glue Up (SaaS 회원 관리) |
| 디렉토리 | /my/directory/corporate/letter/{A-Z}/ |
| 로그인 | 필수 (회원 전용) |
| 보안 | Cloudflare Managed Challenge |

## 2. 접근 방법

- Cloudflare가 Selenium/Playwright 자동화를 차단
- **해결**: Chrome `--remote-debugging-port=9222`로 실행 → 수동 로그인 → Selenium이 기존 세션에 연결
- 별도 `--user-data-dir` 필요 (기존 크롬과 충돌 방지)

## 3. 디렉토리 구조

### 3.1 목록 페이지
- **URL 패턴**: `/my/directory/corporate/letter/{LETTER}/`
- **알파벳 A~Z + # (특수문자)**: 총 27개 탭
- **페이지네이션**: 없음 (한 페이지에 전체 로딩)
- **기업 카드**: `span.company-representation[title]` → title 속성에 회사명
- **B 알파벳 기업 수**: 62개

### 3.2 상세 정보 (오버레이 팝업)
- `button.info-button` 클릭 → `.Overlay.membership-directory-overlay` 팝업
- 팝업 내 `div.labelledListItem` 구조:
  - `div.label` = 필드명
  - `div.value` = 필드값

### 3.3 수집 가능 필드

| 필드 (label) | 예시 값 |
|-------------|---------|
| Company name | B.Braun Vietnam Co., Ltd (h1 또는 card title) |
| Company Profile | 회사 소개 텍스트 |
| Website | http://www.bbraun.com |
| Email Address | info_bpvn@bbraun.com |
| Address | Thanh Oai Industrial Complex, Hanoi |
| Phone | +84 2433571616 |
| 2nd Office Address | 9th Floor, Vinamilk Building... |
| Number of Employees in Vietnam | 1001-2000 |
| Business Category | HEALTH CARE EQUIPMENT, SERVICES 등 |
| Members (담당자) | 이름 + 직책 (Sales Director, CFO 등) |

## 4. 크롤링 전략

### 4.1 프로세스
1. Chrome 디버깅 모드로 실행 (최초 1회 수동 로그인)
2. Selenium으로 디버깅 포트에 연결
3. A~Z 알파벳 순회 → 각 페이지에서 기업 카드 수집
4. 각 기업의 `info-button` 클릭 → 오버레이에서 상세 정보 파싱
5. 오버레이 닫기 → 다음 기업 클릭

### 4.2 기술 요구사항
| 항목 | 내용 |
|------|------|
| 브라우저 | Chrome + remote-debugging-port |
| 자동화 | Selenium (debuggerAddress 연결) |
| 파싱 | BeautifulSoup (오버레이 HTML) |
| 엑셀 | openpyxl |
| 로그인 | 수동 1회 (Cloudflare 우회 불가) |

### 4.3 예상 규모
- 알파벳 27개 탭
- B만 62개 → 전체 추정 약 500~1,000개 기업
- 기업당 info 클릭 + 대기 약 3~5초
- 예상 소요: 약 30분~1시간

## 5. 코참 크롤러와 차이점

| 항목 | 코참 (KOCHAM) | 유럽상의 (EuroCham) |
|------|--------------|-------------------|
| 로그인 | 불필요 | 필수 (수동) |
| Cloudflare | 없음 | Managed Challenge |
| 데이터 로딩 | 정적 HTML | JS 동적 렌더링 |
| 상세 정보 | 별도 페이지 | 오버레이 팝업 |
| 크롤링 방식 | requests + BS4 | Selenium + BS4 |
| 페이지네이션 | 있음 (115p) | 없음 (알파벳별 전체) |
