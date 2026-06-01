BASE_URL = "https://kocham.kr"
LIST_URL = f"{BASE_URL}/theme/inet/sub/sub03_1.php"
DETAIL_URL = f"{BASE_URL}/theme/inet/sub/detail.php"

REQUEST_DELAY = 1.5  # seconds between requests
REQUEST_TIMEOUT = 15  # seconds
MAX_RETRIES = 3

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
}

REGIONS = [
    "", "AN GIANG", "BA RIA-VUNG TAU", "BAC LIEU", "BAC NINH", "BEN TRE",
    "BINH DINH", "BINH DUONG", "BINH PHUOC", "BINH THUAN", "CAN THO",
    "DA NANG", "DAK LAK", "DAK NONG", "DONG NAI", "HA NOI", "HCMC",
    "HUE", "KHANH HOA", "KIEN GIANG", "KON TUM", "LAM DONG", "LONG AN",
    "PHU YEN", "QUANG NAM", "QUANG NGAI", "SOC TRANG", "TAY NINH",
    "TIEN GIANG", "TRA VINH", "VINH LONG",
]

CATEGORIES = {
    "": "전체",
    "1": "농.임업, 광업, 축산, 수산업",
    "2": "제조업",
    "3": "섬유, 신발, 가방 제조업",
    "4": "섬유, 신발, 가방 부자재",
    "5": "건설업",
    "6": "부동산 개발업, 임대업",
    "7": "유통, 도·소매, 무역업",
    "8": "물류, 운수, 여행업",
    "9": "금융, 보험업",
    "10": "법무, 회계, 투자자문",
    "11": "대표사무소, 지사",
    "12": "병원, 의약품",
    "13": "IT, 교육, 대중매체, 광고 관련업",
    "14": "숙박, 요식업, 문화, 스포츠 관련업",
    "15": "인증 / 인력 및 경비용역",
    "16": "기타",
}
