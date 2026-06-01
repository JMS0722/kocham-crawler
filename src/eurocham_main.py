import os
import sys
import time
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from src.eurocham_crawler import EuroChamCrawler, LETTERS, DEBUG_PORT
from src.eurocham_exporter import export_eurocham_excel, generate_eurocham_filename


CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PROFILE_DIR = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Temp", "eurocham_chrome_profile")


class EuroChamApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("EuroCham 디렉토리 크롤러")
        self.root.geometry("750x700")
        self.root.resizable(False, False)

        self.crawler: EuroChamCrawler | None = None
        self.crawl_thread: threading.Thread | None = None
        self._start_time = 0.0
        self._pause_elapsed = 0.0

        self._build_ui()

    def _build_ui(self):
        # Title
        tk.Label(
            self.root, text="EuroCham 디렉토리 크롤러",
            font=("맑은 고딕", 16, "bold"),
        ).pack(pady=(15, 5))
        tk.Label(
            self.root,
            text="European Chamber of Commerce in Vietnam 회원사 정보 수집",
            font=("맑은 고딕", 9), fg="#666",
        ).pack()

        # Chrome connection
        chrome_frame = ttk.LabelFrame(self.root, text="1단계: Chrome 로그인", padding=10)
        chrome_frame.pack(fill="x", padx=20, pady=(15, 5))

        tk.Label(
            chrome_frame,
            text="Chrome을 디버깅 모드로 실행 → EuroCham에 로그인 → 크롤링 시작",
            font=("맑은 고딕", 9), fg="#333",
        ).pack(anchor="w")

        btn_row = tk.Frame(chrome_frame)
        btn_row.pack(fill="x", pady=(5, 0))
        ttk.Button(btn_row, text="Chrome 실행", command=self._launch_chrome).pack(side="left", padx=5)
        ttk.Button(btn_row, text="연결 확인", command=self._check_connection).pack(side="left", padx=5)
        self.conn_status = tk.StringVar(value="미연결")
        tk.Label(btn_row, textvariable=self.conn_status, font=("맑은 고딕", 9), fg="red").pack(side="left", padx=10)

        # Options
        opt_frame = ttk.LabelFrame(self.root, text="크롤링 설정", padding=10)
        opt_frame.pack(fill="x", padx=20, pady=5)

        # Letters
        letter_row = tk.Frame(opt_frame)
        letter_row.pack(fill="x", pady=(0, 5))
        ttk.Label(letter_row, text="알파벳:").pack(side="left")
        self.letter_var = tk.StringVar(value="A-Z (전체)")
        ttk.Combobox(
            letter_row, textvariable=self.letter_var,
            values=["A-Z (전체)"] + list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
            state="readonly", width=15,
        ).pack(side="left", padx=(5, 20))

        ttk.Label(letter_row, text="요청 간격(초):").pack(side="left")
        self.delay_var = tk.DoubleVar(value=2.0)
        ttk.Spinbox(
            letter_row, from_=1.0, to=5.0, increment=0.5,
            textvariable=self.delay_var, width=6,
        ).pack(side="left", padx=5)

        # Profile option
        profile_row = tk.Frame(opt_frame)
        profile_row.pack(fill="x")
        self.include_profile_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            profile_row, text="회사 소개 포함 (앞 200자)",
            variable=self.include_profile_var,
        ).pack(side="left")

        self.auto_open_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            profile_row, text="완료 후 엑셀 자동 열기",
            variable=self.auto_open_var,
        ).pack(side="left", padx=(20, 0))

        # File settings
        file_frame = ttk.LabelFrame(self.root, text="저장 설정", padding=10)
        file_frame.pack(fill="x", padx=20, pady=5)

        path_row = tk.Frame(file_frame)
        path_row.pack(fill="x", pady=(0, 5))
        ttk.Label(path_row, text="저장 경로:").pack(side="left")
        self.save_path_var = tk.StringVar(value=self._get_desktop_path())
        ttk.Entry(path_row, textvariable=self.save_path_var, width=50).pack(side="left", padx=5)
        ttk.Button(path_row, text="찾아보기", command=self._browse_path).pack(side="right")

        name_row = tk.Frame(file_frame)
        name_row.pack(fill="x")
        ttk.Label(name_row, text="파일명:    ").pack(side="left")
        self.filename_var = tk.StringVar(value="EuroCham_Directory")
        ttk.Entry(name_row, textvariable=self.filename_var, width=30).pack(side="left", padx=5)
        ttk.Label(name_row, text="_YYYYMMDD_HHMMSS.xlsx", font=("맑은 고딕", 8), foreground="#999").pack(side="left")

        # Buttons
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)

        self.start_btn = ttk.Button(btn_frame, text="크롤링 시작", command=self._start_crawl)
        self.start_btn.pack(side="left", padx=5)

        self.pause_btn = ttk.Button(btn_frame, text="일시정지", command=self._toggle_pause, state="disabled")
        self.pause_btn.pack(side="left", padx=5)

        self.save_now_btn = ttk.Button(btn_frame, text="중간저장", command=self._save_now, state="disabled")
        self.save_now_btn.pack(side="left", padx=5)

        self.stop_btn = ttk.Button(btn_frame, text="중지", command=self._stop_crawl, state="disabled")
        self.stop_btn.pack(side="left", padx=5)

        # Progress
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            self.root, variable=self.progress_var, maximum=100, length=690,
        )
        self.progress_bar.pack(padx=20, pady=(5, 0))

        self.status_var = tk.StringVar(value="대기 중")
        tk.Label(self.root, textvariable=self.status_var, font=("맑은 고딕", 9)).pack()

        # Log
        log_frame = ttk.LabelFrame(self.root, text="로그", padding=5)
        log_frame.pack(fill="both", expand=True, padx=20, pady=(5, 15))

        self.log_text = tk.Text(log_frame, height=10, font=("Consolas", 9), state="disabled")
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.log_text.pack(fill="both", expand=True)

    # ── Helpers ──

    @staticmethod
    def _get_desktop_path() -> str:
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders",
            )
            desktop, _ = winreg.QueryValueEx(key, "Desktop")
            winreg.CloseKey(key)
            desktop = os.path.expandvars(desktop)
            if os.path.isdir(desktop):
                return desktop
        except Exception:
            pass
        fallback = os.path.join(os.path.expanduser("~"), "Desktop")
        return fallback if os.path.isdir(fallback) else os.path.expanduser("~")

    def _browse_path(self):
        path = filedialog.askdirectory()
        if path:
            self.save_path_var.set(path)

    def _log(self, msg: str):
        def _append():
            self.log_text.configure(state="normal")
            self.log_text.insert("end", msg + "\n")
            self.log_text.see("end")
            self.log_text.configure(state="disabled")
        self.root.after(0, _append)

    def _get_elapsed(self) -> float:
        if self.crawler and self.crawler.is_paused:
            return self._pause_elapsed
        return time.time() - self._start_time

    def _on_progress(self, current: int, total: int, msg: str):
        def _update():
            elapsed = self._get_elapsed()
            elapsed_str = time.strftime("%M:%S", time.gmtime(elapsed))
            if total > 0:
                self.progress_bar.stop()
                self.progress_bar.configure(mode="determinate")
                pct = (current / total) * 100
                self.progress_var.set(pct)
                if current > 0:
                    eta = (elapsed / current) * (total - current)
                    eta_str = time.strftime("%M:%S", time.gmtime(eta))
                    self.status_var.set(f"{msg}  |  경과 {elapsed_str}  |  남은 시간 ~{eta_str}")
                else:
                    self.status_var.set(f"{msg}  |  경과 {elapsed_str}")
            else:
                self.progress_bar.configure(mode="indeterminate")
                self.progress_bar.start(15)
                self.status_var.set(f"{msg}  |  경과 {elapsed_str}")
        self.root.after(0, _update)

    def _build_filepath(self, suffix: str = "") -> str:
        prefix = self.filename_var.get().strip() or "EuroCham_Directory"
        filename = generate_eurocham_filename(prefix=prefix + suffix)
        return os.path.join(self.save_path_var.get(), filename)

    # ── Chrome ──

    def _launch_chrome(self):
        try:
            os.makedirs(PROFILE_DIR, exist_ok=True)
            subprocess.Popen([
                CHROME_PATH,
                f"--remote-debugging-port={DEBUG_PORT}",
                f"--user-data-dir={PROFILE_DIR}",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-features=PrivacySandboxSettings4",
                "--disable-search-engine-choice-screen",
                "--no-service-autorun",
                "https://eurochamvn.glueup.com/account/login",
            ])
            self._log("Chrome 실행됨. 로그인해주세요.")
            self._log(f"디버깅 포트: {DEBUG_PORT}")
            self.conn_status.set("Chrome 실행됨 - 로그인 필요")
        except Exception as e:
            self._log(f"Chrome 실행 실패: {e}")
            messagebox.showerror("에러", f"Chrome 실행 실패:\n{e}")

    def _check_connection(self):
        try:
            opts = Options()
            opts.add_experimental_option("debuggerAddress", f"127.0.0.1:{DEBUG_PORT}")
            driver = webdriver.Chrome(options=opts)
            url = driver.current_url
            if "glueup.com" in url and "/login" not in url:
                self.conn_status.set("연결됨 (로그인 완료)")
                self._log(f"연결 확인: {url}")
                self.root.after(0, lambda: self.conn_status.config(fg="green"))
            else:
                self.conn_status.set("연결됨 (로그인 필요)")
                self._log(f"연결됨, 하지만 로그인 필요: {url}")
                self.root.after(0, lambda: self.conn_status.config(fg="orange"))
        except Exception as e:
            self.conn_status.set("연결 실패")
            self._log(f"연결 실패: {e}")
            self.root.after(0, lambda: self.conn_status.config(fg="red"))

    # ── Actions ──

    def _start_crawl(self):
        save_dir = self.save_path_var.get()
        if not os.path.isdir(save_dir):
            messagebox.showerror("에러", f"저장 경로가 존재하지 않습니다:\n{save_dir}")
            return

        letter_sel = self.letter_var.get()
        if letter_sel == "A-Z (전체)":
            letters = LETTERS
        else:
            letters = [letter_sel]

        self.start_btn.configure(state="disabled")
        self.pause_btn.configure(state="normal", text="일시정지")
        self.save_now_btn.configure(state="normal")
        self.stop_btn.configure(state="normal")
        self.progress_var.set(0)
        self._start_time = time.time()
        self._pause_elapsed = 0.0
        self.progress_bar.configure(mode="determinate")

        self.crawler = EuroChamCrawler(
            letters=letters,
            delay=self.delay_var.get(),
            profile_max_chars=200 if self.include_profile_var.get() else 0,
            include_profile=self.include_profile_var.get(),
            on_progress=self._on_progress,
            on_log=self._log,
        )

        self.crawl_thread = threading.Thread(target=self._run_crawl, daemon=True)
        self.crawl_thread.start()

    def _toggle_pause(self):
        if not self.crawler:
            return
        if self.crawler.is_paused:
            self._start_time = time.time() - self._pause_elapsed
            self.crawler.resume()
            self.pause_btn.configure(text="일시정지")
            self._log("▶ 재개됨")
        else:
            self._pause_elapsed = time.time() - self._start_time
            self.crawler.pause()
            self.pause_btn.configure(text="재개")
            elapsed_str = time.strftime("%M:%S", time.gmtime(self._pause_elapsed))
            self._log(f"⏸ 일시정지 (경과 {elapsed_str})")
            self.status_var.set(f"일시정지 중  |  경과 {elapsed_str}")

    def _stop_crawl(self):
        if self.crawler:
            self.crawler.stop()
            self._log("중지 요청됨...")

    def _save_now(self):
        if not self.crawler or not self.crawler.results:
            messagebox.showwarning("중간저장", "아직 수집된 데이터가 없습니다.")
            return
        try:
            data = list(self.crawler.results)
            path = self._build_filepath(suffix="_partial")
            export_eurocham_excel(data, path, self.include_profile_var.get())
            self._log(f"--- 중간저장 완료: {path} ({len(data)}건) ---")
            messagebox.showinfo("중간저장", f"{len(data)}건 저장 완료\n{path}")
        except Exception as e:
            self._log(f"--- 중간저장 실패: {e} ---")
            messagebox.showerror("중간저장 실패", str(e))

    def _run_crawl(self):
        try:
            results = self.crawler.run()
            if not results:
                self._log("수집된 데이터가 없습니다.")
                self.root.after(0, self._crawl_finished)
                return

            full_path = self._build_filepath()
            try:
                export_eurocham_excel(results, full_path, self.include_profile_var.get())
            except (OSError, PermissionError):
                self._log(f"저장 실패, 다른 경로 선택...")
                result_holder = []
                event = threading.Event()
                def ask():
                    result_holder.append(filedialog.askdirectory(title="저장 경로 선택"))
                    event.set()
                self.root.after(0, ask)
                event.wait(120)
                if result_holder and result_holder[0]:
                    full_path = os.path.join(result_holder[0], os.path.basename(full_path))
                    export_eurocham_excel(results, full_path, self.include_profile_var.get())
                else:
                    self._log("저장 취소됨")
                    self.root.after(0, self._crawl_finished)
                    return

            self._log(f"\n=== 엑셀 저장 완료: {full_path} ===")
            self._log(f"총 {len(results)}개 기업 정보 저장됨")

            if self.auto_open_var.get():
                os.startfile(full_path)

            self.root.after(0, lambda: messagebox.showinfo(
                "완료", f"크롤링 완료!\n{len(results)}개 기업 정보 저장됨\n\n{full_path}"
            ))
        except Exception as e:
            self._log(f"\n[에러] {e}")
            self.root.after(0, lambda: messagebox.showerror("에러", str(e)))
        finally:
            self.root.after(0, self._crawl_finished)

    def _crawl_finished(self):
        self.start_btn.configure(state="normal")
        self.pause_btn.configure(state="disabled", text="일시정지")
        self.save_now_btn.configure(state="disabled")
        self.stop_btn.configure(state="disabled")
        self.progress_bar.stop()
        self.progress_bar.configure(mode="determinate")
        elapsed = self._get_elapsed()
        elapsed_str = time.strftime("%M:%S", time.gmtime(elapsed))
        self.status_var.set(f"완료 (소요 시간: {elapsed_str})")


def main():
    root = tk.Tk()
    app = EuroChamApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
