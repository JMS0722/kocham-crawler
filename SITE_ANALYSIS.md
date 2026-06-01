# 코참(KOCHAM) 디렉토리 사이트 분석 보고서

## 1. 사이트 기본 정보

| 항목 | 내용 |
|------|------|
| 사이트명 | 베트남한인상공인연합회(KOCHAM) |
| URL | https://kocham.kr |
| 정식 명칭 | Korean Chamber of Commerce In Vietnam |
| CMS | 그누보드5 (PHP 기반) |
| 디렉토리 URL | https://kocham.kr/theme/inet/sub/sub03_1.php |
| SSL | DH key 취약 (curl -k 필요) |

## 2. 디렉토리 페이지 구조

### 2.1 목록 페이지
- **URL 패턴**: `https://kocham.kr/theme/inet/sub/sub03_1.php?page={N}`
- **페이지당 항목 수**: 20개
- **총 페이지 수**: 115페이지 (마지막 페이지 16개)
- **총 업체 수 추정**: 약 2,296개 (wr_id 기준 최신: 2296, 최소: ~673)
- **페이지네이션**: 15개씩 구간 표시 (1~15, 16~30, ...)
- **로그인 불필요**: 비회원도 열람 가능

### 2.2 목록에서 표시되는 필드
| 컬럼 | 내용 |
|------|------|
| 번호 | wr_id (내림차순) |
| 업종(대분류) | 업종 카테고리 |
| 지역 | 베트남 내 지역 |
| 업체명 | 영문(한글) + 코참회원 뱃지 |
| 상세업종 | 세부 사업 설명 |

### 2.3 상세 페이지
- **URL 패턴**: `https://kocham.kr/theme/inet/sub/detail.php?wr_id={ID}`
- **수집 가능 필드**:

| 필드 (영문 헤더) | 내용 | 예시 |
|------------------|------|------|
| Company name | 영문명 ( 한글명 ) | COWAY VINA ( 코웨이 비나 ) |
| General Director | 영문이름 ( 한글이름 ) | PARK WON OH ( 박원오 ) |
| Type of business | 대분류 / 소분류 | 유통, 도·소매, 무역업 / 화장품... |
| Tel | 전화번호 | 1800-556-892 |
| Area | 지역 | HCMC |
| Address | 주소 | 9th Fl., Phuong Long 2 Building... |
| E-mail | 이메일 | parkwo@cowayvina.com |
| Homepage | 웹사이트 | https://cowayvina.com.vn/ |
| Number of staff | 직원 수 | 한국인 : 3명 내국인 : 100명 |
| Service | 사업 내용 | 정수기/공기청정기 렌탈... |

## 3. 검색/필터 옵션

### 3.1 업종 대분류 (16개)
1. 농.임업, 광업, 축산, 수산업
2. 제조업
3. 섬유, 신발, 가방 제조업
4. 섬유, 신발, 가방 부자재
5. 건설업
6. 부동산 개발업, 임대업
7. 유통, 도·소매, 무역업
8. 물류, 운수, 여행업
9. 금융, 보험업
10. 법무, 회계, 투자자문
11. 대표사무소, 지사
12. 병원, 의약품
13. IT, 교육, 대중매체, 광고 관련업
14. 숙박, 요식업, 문화, 스포츠 관련업
15. 인증 / 인력 및 경비용역
16. 기타

### 3.2 지역 (31개)
AN GIANG, BA RIA-VUNG TAU, BAC LIEU, BAC NINH, BEN TRE, BINH DINH, BINH DUONG, BINH PHUOC, BINH THUAN, CAN THO, DA NANG, DAK LAK, DAK NONG, DONG NAI, **HA NOI**, **HCMC**, HUE, KHANH HOA, KIEN GIANG, KON TUM, LAM DONG, LONG AN, PHU YEN, QUANG NAM, QUANG NGAI, SOC TRANG, TAY NINH, TIEN GIANG, TRA VINH, VINH LONG

> 호치민(HCMC)과 하노이(HA NOI)가 주요 영업 대상 지역

### 3.3 검색 방식 (POST)
```
POST /theme/inet/sub/sub03_1.php
Parameters:
  - job_gu1: 대분류 번호 (1~16)
  - job_se{N}: 소분류 번호
  - area: 지역명 (예: "HCMC", "HA NOI")
  - word: 검색어 (업체명)
  - order_type: 정렬
```

## 4. 크롤링 전략

### 4.1 접근 방식: 2단계 크롤링
1. **목록 페이지 순회**: page=1 ~ 115 → 각 업체의 wr_id 수집
2. **상세 페이지 접근**: detail.php?wr_id={ID} → 전체 필드 수집

### 4.2 대안 (더 효율적)
- POST 필터로 지역별(HCMC, HA NOI 등) 크롤링 → 영업 대상 지역만 선택 수집
- 페이지 수를 줄이고 타겟팅된 데이터 확보

### 4.3 기술 요구사항
| 항목 | 내용 |
|------|------|
| HTTP 라이브러리 | requests (SSL verify=False 필요) |
| 파싱 | BeautifulSoup4 (정적 HTML, JS 렌더링 불필요) |
| 인증 | 불필요 (비회원 접근 가능) |
| 안티봇 | 없음 (reCAPTCHA는 로그인/회원가입에만 적용) |
| 요청 속도 | 1~2초 딜레이 권장 |

## 5. 예상 수집 결과

| 항목 | 수치 |
|------|------|
| 총 업체 수 | ~2,296개 |
| 상세 페이지 요청 수 | ~2,296회 |
| 예상 소요 시간 (2초 딜레이) | 약 77분 |
| 예상 소요 시간 (1초 딜레이) | 약 38분 |
| 엑셀 파일 크기 | ~500KB 이내 |

## 6. 주의사항

- SSL 인증서 문제로 `verify=False` 설정 필요
- 우클릭/복사 차단 JS 있지만, 크롤러에는 영향 없음
- robots.txt 별도 확인 필요 (SSL 이슈로 접근 제한적)
- 서버 부하 방지를 위해 적절한 딜레이 필수
