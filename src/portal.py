import tkinter as tk
from tkinter import ttk


class PortalApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Vietnam Directory Crawler")
        self.root.geometry("500x400")
        self.root.resizable(False, False)
        self.root.configure(bg="#f5f5f5")

        self._build_ui()

    def _build_ui(self):
        # Title
        header = tk.Frame(self.root, bg="#2C3E50", height=70)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(
            header, text="Vietnam Directory Crawler",
            font=("맑은 고딕", 18, "bold"), fg="white", bg="#2C3E50",
        ).pack(pady=(10, 0))
        tk.Label(
            header, text="베트남 기업 디렉토리 검색 도구",
            font=("맑은 고딕", 10), fg="#BDC3C7", bg="#2C3E50",
        ).pack()

        # Subtitle
        tk.Label(
            self.root, text="크롤링할 디렉토리를 선택하세요",
            font=("맑은 고딕", 11), bg="#f5f5f5", fg="#333",
        ).pack(pady=(25, 15))

        # Cards
        cards_frame = tk.Frame(self.root, bg="#f5f5f5")
        cards_frame.pack(padx=30, fill="x")

        self._create_card(
            cards_frame,
            title="KOCHAM",
            subtitle="베트남한인상공인연합회",
            desc="한국 기업 ~2,300개\n로그인 불필요 | 자동 크롤링",
            color="#2B579A",
            command=self._launch_kocham,
        ).pack(fill="x", pady=(0, 10))

        self._create_card(
            cards_frame,
            title="EuroCham",
            subtitle="European Chamber of Commerce",
            desc="유럽 기업 ~500개\nChrome 로그인 필요",
            color="#1B5E20",
            command=self._launch_eurocham,
        ).pack(fill="x", pady=(0, 10))

        # Footer
        tk.Label(
            self.root,
            text="Vietnam Directory Crawler v1.0",
            font=("맑은 고딕", 8), fg="#999", bg="#f5f5f5",
        ).pack(side="bottom", pady=10)

    def _create_card(self, parent, title, subtitle, desc, color, command):
        card = tk.Frame(parent, bg="white", highlightbackground="#ddd", highlightthickness=1)

        inner = tk.Frame(card, bg="white")
        inner.pack(fill="x", padx=15, pady=12)

        # Left: text
        text_frame = tk.Frame(inner, bg="white")
        text_frame.pack(side="left", fill="x", expand=True)

        tk.Label(
            text_frame, text=title,
            font=("맑은 고딕", 14, "bold"), fg=color, bg="white", anchor="w",
        ).pack(anchor="w")
        tk.Label(
            text_frame, text=subtitle,
            font=("맑은 고딕", 9), fg="#666", bg="white", anchor="w",
        ).pack(anchor="w")
        tk.Label(
            text_frame, text=desc,
            font=("맑은 고딕", 9), fg="#888", bg="white", anchor="w", justify="left",
        ).pack(anchor="w", pady=(3, 0))

        # Right: button
        btn = tk.Button(
            inner, text="실행", font=("맑은 고딕", 10, "bold"),
            fg="white", bg=color, activebackground=color,
            width=8, height=2, relief="flat", cursor="hand2",
            command=command,
        )
        btn.pack(side="right", padx=(10, 0))

        return card

    def _launch_kocham(self):
        self.root.withdraw()
        kocham_root = tk.Toplevel()
        kocham_root.protocol("WM_DELETE_WINDOW", lambda: self._on_child_close(kocham_root))

        from src.main import KochamApp
        KochamApp(kocham_root)

    def _launch_eurocham(self):
        self.root.withdraw()
        eurocham_root = tk.Toplevel()
        eurocham_root.protocol("WM_DELETE_WINDOW", lambda: self._on_child_close(eurocham_root))

        from src.eurocham_main import EuroChamApp
        EuroChamApp(eurocham_root)

    def _on_child_close(self, child):
        child.destroy()
        self.root.deiconify()


def main():
    root = tk.Tk()
    app = PortalApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
