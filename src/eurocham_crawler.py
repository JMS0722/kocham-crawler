import time
import threading
from typing import Callable
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

DEBUG_PORT = 9222
LETTERS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ") + ["-"]


class EuroChamCrawler:
    def __init__(
        self,
        letters: list[str] | None = None,
        delay: float = 2.0,
        profile_max_chars: int = 200,
        include_profile: bool = True,
        on_progress: Callable[[int, int, str], None] | None = None,
        on_log: Callable[[str], None] | None = None,
    ):
        self.letters = letters or LETTERS
        self.delay = delay
        self.profile_max_chars = profile_max_chars
        self.include_profile = include_profile
        self.on_progress = on_progress
        self.on_log = on_log
        self.results: list[dict] = []
        self._stop_flag = False
        self._pause_event = threading.Event()
        self._pause_event.set()
        self.driver = None

    def stop(self):
        self._stop_flag = True
        self._pause_event.set()

    def pause(self):
        self._pause_event.clear()

    def resume(self):
        self._pause_event.set()

    @property
    def is_paused(self) -> bool:
        return not self._pause_event.is_set()

    def _wait_if_paused(self):
        self._pause_event.wait()

    def _log(self, msg: str):
        if self.on_log:
            self.on_log(msg)

    def _progress(self, current: int, total: int, msg: str):
        if self.on_progress:
            self.on_progress(current, total, msg)

    def connect(self) -> bool:
        """Chrome 디버깅 포트에 연결한다."""
        try:
            opts = Options()
            opts.add_experimental_option("debuggerAddress", f"127.0.0.1:{DEBUG_PORT}")
            self.driver = webdriver.Chrome(options=opts)
            self._log(f"Chrome 연결 성공 (port {DEBUG_PORT})")
            self._log(f"현재 URL: {self.driver.current_url}")
            return True
        except Exception as e:
            self._log(f"Chrome 연결 실패: {e}")
            self._log("Chrome을 디버깅 모드로 실행하고 로그인해주세요.")
            return False

    def _parse_overlay(self) -> dict | None:
        """열려있는 오버레이 팝업에서 기업 정보를 파싱한다."""
        try:
            html = self.driver.page_source
            soup = BeautifulSoup(html, "html.parser")
            overlay = soup.select_one(".Overlay.membership-directory-overlay.shown")
            if not overlay:
                return None

            data = {}

            # 회사명
            h1 = overlay.select_one("h1")
            if h1:
                data["company_name"] = h1.get_text(strip=True)

            # 로고 이미지 URL
            logo = overlay.select_one("span.company-representation img")
            if logo:
                data["logo_url"] = logo.get("src", "")

            # labelledListItem 파싱
            for item in overlay.select("div.labelledListItem"):
                label_el = item.select_one("div.label")
                value_el = item.select_one("div.value")
                if not label_el or not value_el:
                    continue

                label = label_el.get_text(strip=True)
                # 링크가 있으면 href 우선
                a_tag = value_el.select_one("a[href]")
                if label == "Website" and a_tag:
                    value = a_tag.get("href", "")
                elif label == "Email Address" and a_tag:
                    value = a_tag.get_text(strip=True)
                elif label == "Phone" and a_tag:
                    value = a_tag.get_text(strip=True)
                else:
                    value = value_el.get_text(strip=True)

                # 필드 매핑
                key_map = {
                    "Company Profile": "profile",
                    "Website": "website",
                    "Email Address": "email",
                    "Address": "address",
                    "Phone": "phone",
                    "2nd Office Address": "address_2nd",
                    "Number of Employees in Vietnam": "employees",
                    "Business Category": "category",
                }
                key = key_map.get(label)
                if key:
                    if key == "profile":
                        if not self.include_profile:
                            continue
                        if self.profile_max_chars and len(value) > self.profile_max_chars:
                            value = value[:self.profile_max_chars] + "..."
                    data[key] = value

            # 담당자 (Members)
            members = []
            for title_el in overlay.select("span.title"):
                name = title_el.get_text(strip=True)
                if not name:
                    continue
                # 바로 다음 형제에서 직책 찾기
                pos_el = title_el.find_next_sibling("span", class_="description")
                position = pos_el.get_text(strip=True) if pos_el else ""
                members.append(f"{name} ({position})" if position else name)
            if members:
                data["members"] = ", ".join(members)

            return data
        except Exception as e:
            self._log(f"  파싱 에러: {e}")
            return None

    def _close_overlay(self):
        """오버레이를 닫는다."""
        # JS로 직접 오버레이 제거 (가장 확실)
        try:
            self.driver.execute_script("""
                var overlay = document.querySelector('.Overlay.membership-directory-overlay.shown');
                if (overlay) {
                    overlay.classList.remove('shown');
                    overlay.style.visibility = 'hidden';
                    overlay.style.opacity = '0';
                }
            """)
            time.sleep(0.3)
            return
        except Exception:
            pass
        # fallback: ESC 키
        try:
            from selenium.webdriver.common.keys import Keys
            self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            time.sleep(0.5)
        except Exception:
            pass

    def crawl_letter(self, letter: str) -> list[dict]:
        """한 알파벳의 기업 목록을 크롤링한다."""
        url = f"https://eurochamvn.glueup.com/my/directory/corporate/letter/{letter}/"
        self.driver.get(url)
        time.sleep(self.delay + 2)

        # 기업 카드 수 확인
        cards = self.driver.find_elements(
            By.CSS_SELECTOR, "span.company-representation[title]"
        )
        info_buttons = self.driver.find_elements(
            By.CSS_SELECTOR, "button.info-button"
        )
        total = len(info_buttons)
        self._log(f"[{letter}] {total}개 기업 발견")

        results = []
        for idx in range(total):
            self._wait_if_paused()
            if self._stop_flag:
                break

            # 매번 다시 찾기 (DOM 갱신 대응)
            buttons = self.driver.find_elements(By.CSS_SELECTOR, "button.info-button")
            if idx >= len(buttons):
                break

            try:
                # 버튼이 보이도록 스크롤
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});", buttons[idx]
                )
                time.sleep(0.3)
                buttons[idx].click()
                time.sleep(self.delay)

                # 오버레이 파싱
                data = self._parse_overlay()
                if data:
                    data["letter"] = letter
                    results.append(data)
                    self._log(f"  [{idx+1}/{total}] {data.get('company_name', 'N/A')}")
                else:
                    self._log(f"  [{idx+1}/{total}] 파싱 실패")

                self._close_overlay()
                time.sleep(0.5)
            except Exception as e:
                self._log(f"  [{idx+1}/{total}] 에러: {e}")
                self._close_overlay()
                time.sleep(1)

        return results

    def run(self) -> list[dict]:
        """전체 크롤링을 실행한다."""
        self._stop_flag = False
        self._pause_event.set()
        self.results = []

        if not self.connect():
            return []

        # 먼저 전체 기업 수 파악
        self._log("=== 알파벳별 기업 수 사전 조회 ===")
        letter_counts = {}
        for letter in self.letters:
            if self._stop_flag:
                break
            url = f"https://eurochamvn.glueup.com/my/directory/corporate/letter/{letter}/"
            self.driver.get(url)
            time.sleep(2)
            buttons = self.driver.find_elements(By.CSS_SELECTOR, "button.info-button")
            letter_counts[letter] = len(buttons)
            self._log(f"  {letter}: {len(buttons)}개")

        total = sum(letter_counts.values())
        self._log(f"=== 총 {total}개 기업 크롤링 시작 ===")
        self._progress(0, total, f"0/{total}")

        done = 0
        for letter in self.letters:
            if self._stop_flag:
                break
            if letter_counts.get(letter, 0) == 0:
                continue

            letter_results = self.crawl_letter(letter)
            self.results.extend(letter_results)
            done += letter_counts[letter]
            self._progress(done, total, f"{done}/{total}")

        self._log(f"=== 총 {len(self.results)}개 기업 정보 수집 완료 ===")
        return self.results
