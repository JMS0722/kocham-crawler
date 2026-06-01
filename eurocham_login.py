"""EuroCham 최초 로그인 스크립트
- 크롬 브라우저가 뜨면 직접 로그인해주세요
- 로그인 완료 후 이 창에서 Enter를 누르면 세션이 저장됩니다
- 이후 크롤러에서 자동으로 이 세션을 재사용합니다
"""
import os
import sys
from selenium import webdriver

PROFILE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chrome_profile")

def main():
    print("=" * 50)
    print("  EuroCham 로그인 세션 설정")
    print("=" * 50)
    print()
    print(f"프로필 경로: {PROFILE_DIR}")
    print()

    opts = webdriver.ChromeOptions()
    opts.add_argument(f"--user-data-dir={PROFILE_DIR}")
    opts.add_argument("--no-first-run")
    opts.add_argument("--no-default-browser-check")
    opts.add_argument("--window-size=1280,900")

    print("Chrome 브라우저를 실행합니다...")
    driver = webdriver.Chrome(options=opts)

    try:
        driver.get("https://eurochamvn.glueup.com/account/login")
        print()
        print(">>> 브라우저에서 다음을 진행해주세요:")
        print("    1. Cloudflare 체크박스 클릭 (있는 경우)")
        print("    2. 이메일/비밀번호 입력 후 로그인")
        print("    3. 로그인 성공 확인")
        print()
        input(">>> 로그인 완료 후 여기서 Enter를 누르세요... ")

        print(f"\n현재 URL: {driver.current_url}")
        print("세션이 저장되었습니다!")
        print("이제 크롤러에서 자동으로 이 세션을 사용합니다.")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
