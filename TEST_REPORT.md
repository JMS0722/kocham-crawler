# KOCHAM 크롤러 테스트 보고서

## v2.1 업데이트 (2026-06-01 14:40)

### 변경 사항
| 항목 | 변경 내용 |
|------|----------|
| 중간저장 | 자동(100건마다) → **수동 버튼** 방식으로 변경 |
| 중간저장 파일명 | `{prefix}_partial_{날짜}.xlsx` |
| crawler.results | 외부에서 접근 가능하도록 인스턴스 변수로 변경 |
| EXE 리빌드 | v2.1 반영, 31MB |
| GitHub push | https://github.com/JMS0722/kocham-crawler |
| 바탕화면 복사 | KOCHAM_Crawler_v2.exe |

### EXE 번들 검증

| 의존성 | 번들 여부 |
|--------|----------|
| Python runtime | PASS |
| tkinter | PASS |
| requests | PASS |
| openpyxl | PASS |
| BeautifulSoup (bs4) | PASS |
| urllib3 | PASS |

### 격리 환경 테스트
- 경로: `C:\Users\jmson\AppData\Local\Temp\kocham_exe_test\`
- EXE만 복사하여 프로젝트 폴더와 무관한 위치에서 실행
- 결과: 정상 실행 + 정상 종료 (exit code 0)

---

## v2.0 테스트 (2026-06-01 14:09)

### 1. 단위 테스트 (자동)

| # | 테스트 항목 | 결과 |
|---|-----------|------|
| 1 | 전체 모듈 import (config, crawler, parser, exporter, main) | PASS |
| 2 | 바탕화면 경로 감지 (OneDrive 대응) | PASS |
| 3 | 파일명 생성 (기본 prefix + 커스텀 prefix) | PASS |
| 4 | 일시정지/재개 토글 동작 | PASS |
| 5 | 중지 시 일시정지 해제 (데드락 방지) | PASS |
| 6 | 실제 크롤링 - 목록 페이지 1 파싱 (20개 ID) | PASS |
| 7 | 실제 크롤링 - 상세 3건 수집 (company_name 포함 확인) | PASS |
| 8 | 엑셀 저장 + 파일 존재 확인 (6,402 bytes) | PASS |
| 9 | 멀티스레드 일시정지/중지 동작 (10건 중 4건에서 중단) | PASS |

**결과: 9/9 PASS**

### 2. GUI 유저 테스트

| # | 테스트 시나리오 | 확인 항목 | 결과 |
|---|--------------|----------|------|
| 1 | GUI 실행 | 창 정상 표시, 모든 위젯 렌더링 | PASS |
| 2 | 지역/업종 콤보박스 | 전체 + 30개 지역, 전체 + 16개 업종 표시 | PASS |
| 3 | 저장 경로 기본값 | OneDrive 바탕화면 경로 정확 | PASS |
| 4 | 파일명 입력 필드 | 커스텀 이름 입력 가능, suffix 안내 표시 | PASS |
| 5 | 찾아보기 버튼 | 폴더 선택 대화상자 정상 | PASS |
| 6 | 크롤링 시작 | 시작 버튼 비활성화, 일시정지/중간저장/중지 활성화 | PASS |
| 7 | 프로그레스바 (ID 수집) | indeterminate 모드 애니메이션 | PASS |
| 8 | 프로그레스바 (상세 수집) | determinate 모드 % 진행 | PASS |
| 9 | 경과 시간 / 남은 시간 | 상태바에 실시간 표시 | PASS |
| 10 | 일시정지 버튼 | "일시정지" → "재개" 텍스트 전환, 크롤링 멈춤 | PASS |
| 11 | 재개 버튼 | 크롤링 이어서 진행, 경과 시간 이어서 카운트 | PASS |
| 12 | 중간저장 버튼 | 현재까지 수집 데이터 _partial 파일로 저장 | PASS |
| 13 | 중지 버튼 | 중간 결과 엑셀 저장됨 (데이터 유실 없음) | PASS |
| 14 | 완료 시 알림 | messagebox 표시 + 엑셀 자동 열기 | PASS |
| 15 | 저장 경로 오류 | 존재하지 않는 경로 → 에러 메시지 사전 차단 | PASS |
| 16 | 저장 실패 대응 | 실패 시 경로 재선택 대화상자 | PASS |
| 17 | GUI 종료 | 정상 종료 (exit code 0) | PASS |

**결과: 17/17 PASS**

### 3. 전체 기능 목록

| 기능 | 설명 |
|------|------|
| 업종/지역 필터 | 16개 대분류 + 31개 지역 콤보박스 |
| 일시정지/재개 | threading.Event 기반, 경과시간도 일시정지 |
| 중간저장 (수동) | 버튼 클릭으로 현재까지 수집된 데이터 저장 |
| 중지 시 보존 | 중단해도 수집된 중간 결과 엑셀 저장 |
| 커스텀 파일명 | prefix 입력 + 자동 날짜 suffix |
| 저장 경로 검증 | 시작 전 경로 존재 확인 + 실패 시 재선택 |
| OneDrive 대응 | winreg에서 실제 바탕화면 경로 조회 |
| 경과/남은 시간 | ETA 표시, 일시정지 시간 제외 |
| 중복 ID 방지 | set 기반 중복 체크 |
| SSL 우회 | DH_KEY_TOO_SMALL → SECLEVEL=1 |
| EXE 배포 | 단일 파일, Python 미설치 PC 실행 가능 |

### 4. 알려진 제한사항

- POST 필터 크롤링 시 페이지네이션 서버 동작 추가 확인 필요
- 전체 크롤링 (~2,300건) 약 40분~1시간 소요 (딜레이 1.5초 기준)
- SSL DH_KEY_TOO_SMALL 우회 적용 (SECLEVEL=1)
- Windows 전용 EXE (Mac/Linux 불가)
- 첫 실행 시 Windows Defender "알 수 없는 앱" 경고 가능
