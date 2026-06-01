# 작업 히스토리

## 2026-06-01 (Day 1) — 프로젝트 생성 + 전체 개발

### 1. KOCHAM 크롤러 개발

#### 1.1 사이트 분석
- 코참(KOCHAM) 디렉토리 사이트 구조 분석
- URL 패턴: sub03_1.php (목록) → detail.php?wr_id={ID} (상세)
- 총 ~2,296개 업체, 115페이지, 로그인 불필요
- SSL DH_KEY_TOO_SMALL 이슈 발견 → SECLEVEL=1 우회
- 분석 결과: SITE_ANALYSIS.md

#### 1.2 크롤링 엔진 (v1)
- requests + BeautifulSoup4 기반
- 업종(16개)/지역(31개) 필터링
- 페이지네이션 자동 처리
- 재시도 로직 (3회)

#### 1.3 코드 리뷰 + 개선 (v2)
- 프로그레스바 버그 수정 (ID 수집 단계 indeterminate 모드)
- 중지 시 중간 결과 보존 (기존: 전부 유실)
- 중복 ID 방지 (set 기반)
- 경과시간 + 남은시간 ETA 표시
- 일시정지/재개 기능 (threading.Event)

#### 1.4 저장 경로 이슈 수정
- OneDrive 바탕화면 이동 환경에서 Desktop 경로 불일치
- winreg에서 실제 경로 조회하도록 수정
- 저장 실패 시 경로 재선택 대화상자 추가

#### 1.5 중간저장 (v2.1)
- 자동 100건마다 → 수동 버튼 방식으로 변경 (사용자 요청)
- crawler.results 외부 접근 가능하도록 변경

#### 1.6 EXE 빌드
- PyInstaller --onefile --windowed
- 31MB, Python 미설치 PC에서 실행 가능
- 격리 환경(temp 폴더) 테스트 통과

#### 1.7 테스트
- 단위 테스트 9/9 PASS
- GUI 테스트 17/17 PASS
- EXE 번들 검증 (Python, tkinter, requests, openpyxl, bs4, urllib3)
- 결과: TEST_REPORT.md

---

### 2. EuroCham 크롤러 개발

#### 2.1 사이트 분석
- Glue Up SaaS 플랫폼, Cloudflare Managed Challenge
- 로그인 필수, JS 동적 렌더링
- Selenium/Playwright 직접 로그인 시도 → Cloudflare 차단
- 해결: Chrome --remote-debugging-port=9222 → 수동 로그인 → Selenium 연결

#### 2.2 페이지 구조 파악
- 디렉토리: /my/directory/corporate/letter/{A-Z}/
- 기업 카드: span.company-representation[title]
- 상세: button.info-button 클릭 → 오버레이 팝업
- 필드: div.labelledListItem > div.label + div.value
- B 알파벳 62개 기업 확인

#### 2.3 크롤러 구현
- Selenium + BeautifulSoup 하이브리드
- Chrome 디버깅 포트 연결 방식
- A-Z 알파벳 순회 + 개별 선택
- 오버레이 JS 제거 방식으로 닫기
- Company Profile 앞 200자 자르기 (옵션)

#### 2.4 버그 수정
- `Options` / `webdriver` import 누락 수정
- onboardingModal 자동 제거 (JS)
- info-button JS 클릭으로 변경 (모달 차단 우회)
- Chrome 프로필 설정 화면 스킵 플래그 추가

#### 2.5 테스트
- B 알파벳 5/5 기업 수집 성공
- 필드: company_name, email, phone, address, website, employees, category, members, profile

---

### 3. 포털 프로그램

#### 3.1 통합 런처
- KOCHAM / EuroCham 선택 실행
- 크롤러 닫으면 포털로 복귀
- 브랜딩: Vietnam Directory Crawler (중립)

---

### 4. 파일명 규칙
- 코참: `코참디렉토리_{지역}_{일시}.xlsx`
- 유로참: `유로참디렉토리_{알파벳}_{일시}.xlsx`
- 중간저장: `_partial` suffix 추가

---

### 5. Git 커밋 이력

| 커밋 | 내용 |
|------|------|
| 7bc8b54 | Initial commit: KOCHAM Directory Crawler v2 |
| 2b520b7 | v2.1: Manual save button, test report update |
| 602a33a | Add EuroCham directory crawler |
| 88a37ae | Fix: modal dismiss, Options import, portal branding |
| f476401 | Fix: add webdriver import to eurocham_main.py |
| 233aa51 | 파일명 자동 생성 규칙 적용 |

---

### 6. 프로젝트 파일 구조 (최종)

```
kocham-crawler/
├── run.py                  # KOCHAM 크롤러 진입점
├── run_eurocham.py         # EuroCham 크롤러 진입점
├── run_portal.py           # 포털 진입점
├── requirements.txt
├── build.spec
├── src/
│   ├── __init__.py
│   ├── config.py           # KOCHAM 설정
│   ├── crawler.py          # KOCHAM 크롤링 엔진
│   ├── parser.py           # KOCHAM HTML 파싱
│   ├── exporter.py         # KOCHAM 엑셀 출력
│   ├── main.py             # KOCHAM GUI
│   ├── eurocham_crawler.py # EuroCham 크롤링 엔진
│   ├── eurocham_exporter.py# EuroCham 엑셀 출력
│   ├── eurocham_main.py    # EuroCham GUI
│   └── portal.py           # 포털 런처
├── PROJECT_PLAN.md
├── SITE_ANALYSIS.md
├── EUROCHAM_ANALYSIS.md
├── TEST_REPORT.md
├── CHANGELOG.md            # 본 문서
└── dist/
    └── VN_Directory_Crawler.exe
```
