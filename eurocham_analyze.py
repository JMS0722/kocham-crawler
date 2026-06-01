"""EuroCham 디렉토리 사이트 분석 (Playwright + stealth)"""
import time
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
from bs4 import BeautifulSoup

EMAIL = "hoangthi.tham@lottevn.net"
PASSWORD = "Lotte@2026"


def run():
    with sync_playwright() as p:
        print("1) Chromium 실행 중...")
        browser = p.chromium.launch(headless=False, slow_mo=100)
        stealth = Stealth()
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.7778.179 Safari/537.36",
        )
        stealth.apply_stealth_sync(context)
        page = context.new_page()

        # 1) 로그인
        print("2) 로그인 페이지 로딩...")
        page.goto("https://eurochamvn.glueup.com/account/login", wait_until="domcontentloaded")

        print("3) Cloudflare 통과 대기 (최대 3분)...")
        try:
            page.wait_for_selector(
                'input[type="email"], input[name="email"], input#email',
                timeout=180000,
            )
            print("   로그인 폼 발견!")
        except Exception:
            print(f"   타임아웃. URL: {page.url}")
            print(f"   Title: {page.title()}")
            page.screenshot(path="cf_fail.png")
            print("   스크린샷 저장: cf_fail.png")
            browser.close()
            return

        print("4) 로그인 정보 입력...")
        page.fill('input[type="email"], input[name="email"]', EMAIL)
        page.fill('input[type="password"]', PASSWORD)
        time.sleep(0.5)

        print("5) 로그인 클릭...")
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle", timeout=30000)
        time.sleep(3)
        print(f"   로그인 후 URL: {page.url}")

        # 2) 디렉토리 A
        print("\n6) 디렉토리 A 페이지...")
        page.goto("https://eurochamvn.glueup.com/my/directory/corporate/letter/A/", wait_until="networkidle")
        time.sleep(3)

        html_a = page.content()
        with open("eurocham_directory_A.html", "w", encoding="utf-8") as f:
            f.write(html_a)

        soup_a = BeautifulSoup(html_a, "html.parser")
        all_links = soup_a.select("a[href]")
        letter_links = [a for a in all_links if "/letter/" in a.get("href", "")]
        org_links = [a for a in all_links if "/organization/" in a.get("href", "")]

        print(f"   전체 링크: {len(all_links)}")
        print(f"   알파벳 링크: {len(letter_links)}")
        print(f"   기업 링크: {len(org_links)}")

        print("\n   --- 알파벳 네비게이션 ---")
        seen_letters = set()
        for l in letter_links:
            txt = l.get_text(strip=True)
            if txt not in seen_letters:
                seen_letters.add(txt)
                print(f"   {txt} -> {l['href']}")

        print(f"\n   --- A 기업 목록 (총 {len(org_links)}개) ---")
        for l in org_links[:10]:
            print(f"   {l.get_text(strip=True)[:60]} -> {l['href']}")

        # 3) 디렉토리 B
        print("\n7) 디렉토리 B 페이지...")
        page.goto("https://eurochamvn.glueup.com/my/directory/corporate/letter/B/", wait_until="networkidle")
        time.sleep(3)
        html_b = page.content()
        with open("eurocham_directory_B.html", "w", encoding="utf-8") as f:
            f.write(html_b)
        soup_b = BeautifulSoup(html_b, "html.parser")
        org_links_b = [a for a in soup_b.select("a[href]") if "/organization/" in a.get("href", "")]
        print(f"   B 기업 수: {len(org_links_b)}")

        # 페이지네이션 확인
        page_links = [a for a in soup_b.select("a[href]") if "page=" in a.get("href", "")]
        print(f"   페이지 링크: {len(page_links)}")
        for pl in page_links[:5]:
            print(f"   {pl.get_text(strip=True)} -> {pl['href']}")

        # 4) 상세 페이지
        if org_links_b:
            href = org_links_b[0]["href"]
            if not href.startswith("http"):
                href = "https://eurochamvn.glueup.com" + href
            print(f"\n8) 상세 페이지: {href}")
            page.goto(href, wait_until="networkidle")
            time.sleep(3)

            html_d = page.content()
            with open("eurocham_detail_sample.html", "w", encoding="utf-8") as f:
                f.write(html_d)

            soup_d = BeautifulSoup(html_d, "html.parser")
            for tag in ["h1", "h2", "h3"]:
                for el in soup_d.select(tag)[:3]:
                    print(f"   <{tag}> {el.get_text(strip=True)[:80]}")

            tables = soup_d.select("table")
            dls = soup_d.select("dl, dt, dd")
            labels = soup_d.select("[class*=label], [class*=field], [class*=info]")
            print(f"   테이블: {len(tables)}, DL: {len(dls)}, Label요소: {len(labels)}")
            for lb in labels[:10]:
                print(f"     {lb.name}.{lb.get('class','')} = {lb.get_text(strip=True)[:60]}")

        # 5) 전체 알파벳 카운트
        print("\n9) 전체 알파벳별 기업 수...")
        counts = {"A": len(org_links), "B": len(org_links_b)}
        for letter in "CDEFGHIJKLMNOPQRSTUVWXYZ":
            url = f"https://eurochamvn.glueup.com/my/directory/corporate/letter/{letter}/"
            page.goto(url, wait_until="networkidle")
            time.sleep(2)
            soup_tmp = BeautifulSoup(page.content(), "html.parser")
            cnt = len([a for a in soup_tmp.select("a[href]") if "/organization/" in a.get("href", "")])
            counts[letter] = cnt
            print(f"   {letter}: {cnt}")

        total = sum(counts.values())
        print(f"\n=== 총 기업 수: {total} ===")

        print("\n분석 완료!")
        browser.close()


if __name__ == "__main__":
    run()
