import os
import sys
import time
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from src.config import REGIONS, CATEGORIES
from src.crawler import KochamCrawler
from src.exporter import export_to_excel, generate_filename


class KochamApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("KOCHAM 디렉토리 크롤러")
        self.root.geometry("720x650")
        self.root.resizable(False, False)

        self.crawler: KochamCrawler | None = None
        self.crawl_thread: threading.Thread | None = None
        self._start_time = 0.0
        self._pause_elapsed = 0.0  # 일시정지 시 경과시간 보존용

        self._build_ui()

    def _build_ui(self):
        # --- Title ---
        title = tk.Label(
            self.root, text="KOCHAM 디렉토리 크롤러",
            font=("맑은 고딕", 16, "bold"),
        )
        title.pack(pady=(15, 5))
        subtitle = tk.Label(
            self.root,
            text="베트남한인상공인연합회 회원사 정보 수집 → Excel 저장",
            font=("맑은 고딕", 9), fg="#666",
        )
        subtitle.pack()

        # --- Filter Frame ---
        filter_frame = ttk.LabelFrame(self.root, text="검색 필터", padding=10)
        filter_frame.pack(fill="x", padx=20, pady=(15, 5))

        ttk.Label(filter_frame, text="지역:").grid(row=0, column=0, sticky="w", padx=(0, 5))
        self.region_var = tk.StringVar(value="")
        region_combo = ttk.Combobox(
            filter_frame, textvariable=self.region_var,
            values=["전체"] + [r for r in REGIONS if r],
            state="readonly", width=25,
        )
        region_combo.current(0)
        region_combo.grid(row=0, column=1, padx=(0, 20))

        ttk.Label(filter_frame, text="업종:").grid(row=0, column=2, sticky="w", padx=(0, 5))
        self.cat_var = tk.StringVar(value="")
        cat_values = [CATEGORIES[k] for k in CATEGORIES]
        self.cat_combo = ttk.Combobox(
            filter_frame, textvariable=self.cat_var,
            values=cat_values, state="readonly", width=30,
        )
        self.cat_combo.current(0)
        self.cat_combo.grid(row=0, column=3)

        # --- File Settings ---
        file_frame = ttk.LabelFrame(self.root, text="저장 설정", padding=10)
        file_frame.pack(fill="x", padx=20, pady=5)

        # Save path
        path_row = tk.Frame(file_frame)
        path_row.pack(fill="x", pady=(0, 5))
        ttk.Label(path_row, text="저장 경로:").pack(side="left")
        self.save_path_var = tk.StringVar(value=self._get_desktop_path())
        ttk.Entry(path_row, textvariable=self.save_path_var, width=52).pack(side="left", padx=(5, 5))
        ttk.Button(path_row, text="찾아보기", command=self._browse_path).pack(side="right")

        # Filename preview
        name_row = tk.Frame(file_frame)
        name_row.pack(fill="x")
        ttk.Label(name_row, text="파일명:    ").pack(side="left")
        ttk.Label(name_row, text="코참디렉토리_{지역}_{일시}.xlsx", font=("맑은 고딕", 9), foreground="#666").pack(side="left")

        # --- Delay ---
        delay_frame = ttk.LabelFrame(self.root, text="요청 설정", padding=10)
        delay_frame.pack(fill="x", padx=20, pady=5)

        ttk.Label(delay_frame, text="요청 간격(초):").pack(side="left")
        self.delay_var = tk.DoubleVar(value=1.5)
        ttk.Spinbox(
            delay_frame, from_=0.5, to=5.0, increment=0.5,
            textvariable=self.delay_var, width=6,
        ).pack(side="left", padx=(5, 20))

        self.auto_open_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            delay_frame, text="완료 후 엑셀 파일 자동 열기",
            variable=self.auto_open_var,
        ).pack(side="left")

        # --- Buttons ---
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

        # --- Progress ---
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            self.root, variable=self.progress_var,
            maximum=100, length=660,
        )
        self.progress_bar.pack(padx=20, pady=(5, 0))

        self.status_var = tk.StringVar(value="대기 중")
        tk.Label(self.root, textvariable=self.status_var, font=("맑은 고딕", 9)).pack()

        # --- Log ---
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
        """Windows 바탕화면 실제 경로를 반환한다 (OneDrive 이동 대응)."""
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
        if os.path.isdir(fallback):
            return fallback
        return os.path.expanduser("~")

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
        """일시정지 시간을 제외한 실제 경과 시간"""
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

    def _get_selected_category_key(self) -> str:
        selected = self.cat_var.get()
        for key, val in CATEGORIES.items():
            if val == selected:
                return key
        return ""

    def _build_filepath(self, suffix: str = "") -> str:
        """파일명 생성. 코참디렉토리_일자_지역"""
        region = self.region_var.get()
        if region == "전체" or not region:
            region_tag = "전체"
        else:
            region_tag = region
        prefix = f"코참디렉토리_{region_tag}"
        filename = generate_filename(prefix=prefix + suffix)
        return os.path.join(self.save_path_var.get(), filename)

    # ── Actions ──

    def _start_crawl(self):
        # 저장 경로 사전 검증
        save_dir = self.save_path_var.get()
        if not os.path.isdir(save_dir):
            messagebox.showerror("에러", f"저장 경로가 존재하지 않습니다:\n{save_dir}")
            return

        region = self.region_var.get()
        if region == "전체":
            region = ""
        category = self._get_selected_category_key()

        self.start_btn.configure(state="disabled")
        self.pause_btn.configure(state="normal", text="일시정지")
        self.save_now_btn.configure(state="normal")
        self.stop_btn.configure(state="normal")
        self.progress_var.set(0)
        self._start_time = time.time()
        self._pause_elapsed = 0.0
        self.progress_bar.configure(mode="determinate")

        self.crawler = KochamCrawler(
            region=region,
            category=category,
            delay=self.delay_var.get(),
            on_progress=self._on_progress,
            on_log=self._log,
        )

        self.crawl_thread = threading.Thread(target=self._run_crawl, daemon=True)
        self.crawl_thread.start()

    def _toggle_pause(self):
        if not self.crawler:
            return
        if self.crawler.is_paused:
            # 재개: 시작시간을 보정해서 경과시간 이어가기
            self._start_time = time.time() - self._pause_elapsed
            self.crawler.resume()
            self.pause_btn.configure(text="일시정지")
            self._log("▶ 재개됨")
            self.status_var.set("재개됨...")
        else:
            # 일시정지: 현재 경과시간 저장
            self._pause_elapsed = time.time() - self._start_time
            self.crawler.pause()
            self.pause_btn.configure(text="재개")
            elapsed_str = time.strftime("%M:%S", time.gmtime(self._pause_elapsed))
            self._log(f"⏸ 일시정지 (경과 {elapsed_str})")
            self.status_var.set(f"일시정지 중  |  경과 {elapsed_str}")

    def _stop_crawl(self):
        if self.crawler:
            self.crawler.stop()
            self._log("중지 요청됨... 현재 작업 완료 후 중단됩니다.")

    def _save_now(self):
        """중간저장 버튼 클릭 핸들러"""
        if not self.crawler or not self.crawler.results:
            messagebox.showwarning("중간저장", "아직 수집된 데이터가 없습니다.")
            return
        try:
            data = list(self.crawler.results)
            path = self._build_filepath(suffix="_partial")
            export_to_excel(data, path)
            self._log(f"--- 중간저장 완료: {path} ({len(data)}건) ---")
            messagebox.showinfo("중간저장", f"{len(data)}건 저장 완료\n{path}")
        except Exception as e:
            self._log(f"--- 중간저장 실패: {e} ---")
            messagebox.showerror("중간저장 실패", str(e))

    def _save_results(self, results: list[dict]) -> str | None:
        """엑셀 저장 시도. 실패하면 사용자에게 다른 경로를 선택하게 한다."""
        full_path = self._build_filepath()
        try:
            export_to_excel(results, full_path)
            return full_path
        except (OSError, PermissionError) as e:
            self._log(f"\n[저장 실패] {full_path} - {e}")
            self._log("다른 저장 경로를 선택합니다...")
            result_holder = []
            event = threading.Event()

            def ask_path():
                new_dir = filedialog.askdirectory(title="엑셀 저장 경로를 다시 선택하세요")
                result_holder.append(new_dir)
                event.set()

            self.root.after(0, ask_path)
            event.wait(timeout=120)

            if result_holder and result_holder[0]:
                fallback_path = os.path.join(result_holder[0], os.path.basename(full_path))
                try:
                    export_to_excel(results, fallback_path)
                    return fallback_path
                except Exception as e2:
                    self._log(f"[저장 재실패] {e2}")
            return None

    def _run_crawl(self):
        try:
            results = self.crawler.run()
            if not results:
                self._log("수집된 데이터가 없습니다.")
                self.root.after(0, self._crawl_finished)
                return

            full_path = self._save_results(results)

            if full_path:
                self._log(f"\n=== 엑셀 저장 완료: {full_path} ===")
                self._log(f"총 {len(results)}개 기업 정보 저장됨")

                if self.auto_open_var.get():
                    os.startfile(full_path)

                self.root.after(0, lambda: messagebox.showinfo(
                    "완료", f"크롤링 완료!\n{len(results)}개 기업 정보 저장됨\n\n{full_path}"
                ))
            else:
                self._log("\n[에러] 엑셀 저장에 실패했습니다.")
                self.root.after(0, lambda: messagebox.showerror(
                    "저장 실패", "엑셀 파일 저장에 실패했습니다.\n다시 크롤링해주세요."
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
    app = KochamApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
