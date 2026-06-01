import ssl
import time
import threading
import urllib3
import requests
from requests.adapters import HTTPAdapter
from typing import Callable

from src.config import (
    LIST_URL, DETAIL_URL, HEADERS,
    REQUEST_DELAY, REQUEST_TIMEOUT, MAX_RETRIES,
)
from src.parser import parse_list_page, parse_detail_page

# suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)



class UnsafeSSLAdapter(HTTPAdapter):
    """SSL 보안 수준을 낮춰 DH_KEY_TOO_SMALL 에러를 우회한다."""
    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        ctx.set_ciphers("DEFAULT:@SECLEVEL=1")
        kwargs["ssl_context"] = ctx
        return super().init_poolmanager(*args, **kwargs)


class KochamCrawler:
    def __init__(
        self,
        region: str = "",
        category: str = "",
        delay: float = REQUEST_DELAY,
        on_progress: Callable[[int, int, str], None] | None = None,
        on_log: Callable[[str], None] | None = None,
    ):
        self.region = region
        self.category = category
        self.delay = delay
        self.on_progress = on_progress  # (current, total, message)
        self.on_log = on_log
        self.results: list[dict] = []  # 외부에서 중간저장 시 접근
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.session.verify = False
        self.session.mount("https://", UnsafeSSLAdapter())
        self._stop_flag = False
        self._pause_event = threading.Event()
        self._pause_event.set()  # 기본: 실행 상태

    def stop(self):
        self._stop_flag = True
        self._pause_event.set()  # 일시정지 중이면 풀어서 종료되게

    def pause(self):
        self._pause_event.clear()

    def resume(self):
        self._pause_event.set()

    @property
    def is_paused(self) -> bool:
        return not self._pause_event.is_set()

    def _wait_if_paused(self):
        """일시정지 상태면 재개될 때까지 대기"""
        self._pause_event.wait()

    def _log(self, msg: str):
        if self.on_log:
            self.on_log(msg)

    def _progress(self, current: int, total: int, msg: str):
        if self.on_progress:
            self.on_progress(current, total, msg)

    def _request(self, url: str, method: str = "GET", data: dict = None) -> str | None:
        """HTTP 요청 + 재시도 로직"""
        for attempt in range(MAX_RETRIES):
            try:
                if method == "POST":
                    resp = self.session.post(url, data=data, timeout=REQUEST_TIMEOUT)
                else:
                    resp = self.session.get(url, params=data, timeout=REQUEST_TIMEOUT)
                resp.encoding = "utf-8"
                return resp.text
            except requests.RequestException as e:
                self._log(f"[재시도 {attempt+1}/{MAX_RETRIES}] {url} - {e}")
                time.sleep(2)
        self._log(f"[실패] {url}")
        return None

    def collect_ids(self) -> list[int]:
        """전체 목록을 순회하여 wr_id를 수집한다."""
        all_ids = []
        seen = set()
        page = 1
        self._log("=== wr_id 수집 시작 ===")

        while not self._stop_flag:
            self._wait_if_paused()
            if self._stop_flag:
                break

            self._log(f"목록 페이지 {page} 크롤링 중...")

            if self.region or self.category:
                post_data = {
                    "job_gu1": self.category,
                    "area": self.region,
                    "word": "",
                    "order_type": "",
                }
                url = f"{LIST_URL}?page={page}"
                html = self._request(url, method="POST", data=post_data)
            else:
                html = self._request(f"{LIST_URL}?page={page}")

            if not html:
                break

            ids = parse_list_page(html)
            if not ids:
                break

            new_count = 0
            for wid in ids:
                if wid not in seen:
                    seen.add(wid)
                    all_ids.append(wid)
                    new_count += 1

            if new_count == 0:
                break

            self._progress(0, 0, f"ID 수집 중... ({len(all_ids)}개, 페이지 {page})")
            page += 1
            time.sleep(self.delay)

        self._log(f"=== 총 {len(all_ids)}개 업체 ID 수집 완료 ===")
        return all_ids

    def collect_details(self, wr_ids: list[int]) -> list[dict]:
        """상세 페이지에서 기업 정보를 수집한다."""
        self.results = []
        total = len(wr_ids)
        self._log(f"=== 상세 정보 수집 시작 (총 {total}개) ===")
        self._progress(0, total, f"0/{total}")

        for idx, wr_id in enumerate(wr_ids, 1):
            self._wait_if_paused()
            if self._stop_flag:
                self._log("사용자에 의해 중단됨")
                break

            html = self._request(DETAIL_URL, data={"wr_id": wr_id})
            if html:
                detail = parse_detail_page(html, wr_id)
                self.results.append(detail)
                name = detail.get("company_name", "N/A")
                self._log(f"[{idx}/{total}] {name}")
            else:
                self.results.append({"wr_id": wr_id})
                self._log(f"[{idx}/{total}] wr_id={wr_id} - 수집 실패")

            self._progress(idx, total, f"{idx}/{total}")
            time.sleep(self.delay)

        self._log(f"=== 총 {len(self.results)}개 기업 정보 수집 완료 ===")
        return self.results

    def run(self) -> list[dict]:
        """전체 크롤링 프로세스를 실행한다."""
        self._stop_flag = False
        self._pause_event.set()
        wr_ids = self.collect_ids()
        if not wr_ids:
            return []
        if self._stop_flag:
            return []
        results = self.collect_details(wr_ids)
        # 중지된 경우에도 수집된 중간 결과를 반환
        return results
