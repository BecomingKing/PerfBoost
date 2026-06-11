"""主应用窗口：左侧导航栏 + 右侧内容区."""

import time
import customtkinter as ctk

from core.monitor import SystemMonitor
from core.tray import SystemTray
from utils.config import Config
from utils.helpers import get_boot_time, get_theme_from_registry
from ui.dashboard import DashboardFrame
from ui.disk_analyzer import DiskAnalyzerFrame
from ui.cleaner import CleanerFrame
from ui.startup import StartupFrame
from ui.process import ProcessFrame
from ui.settings import SettingsFrame


SIDEBAR_WIDTH = 170
NAV_ITEMS = [
    ("仪表盘", "dashboard"),
    ("清理", "cleaner"),
    ("启动项", "startup"),
    ("进程", "process"),
    ("磁盘分析", "disk_analyzer"),
    ("设置", "settings"),
]


class PerfBoostApp:
    def __init__(self):
        self.config = Config()
        self.monitor = SystemMonitor(interval=self.config.get("monitor_interval", 1))

        self._apply_theme()
        ctk.set_default_color_theme("blue")

        self.root = ctk.CTk()
        self.root.title("PerfBoost - 系统性能优化")
        self.root.geometry("820x600")
        self.root.minsize(700, 500)

        self.tray = SystemTray(
            on_show=self._show_window,
            on_hide=self._hide_to_tray,
            on_exit=self._quit_app,
            monitor=None,
        )

        self._build_layout()
        self._build_sidebar()
        self._build_pages()
        self._navigate_to("dashboard")

        self.monitor.start()
        self._poll_monitor()
        self.root.protocol("WM_DELETE_WINDOW", self._quit_app)

    def _apply_theme(self):
        theme = self.config.get("theme", "system")
        if theme == "system":
            theme = get_theme_from_registry()
        ctk.set_appearance_mode(theme)

    # ---- 布局 ----

    def _build_layout(self):
        self.body = ctk.CTkFrame(self.root, fg_color="transparent")
        self.body.pack(fill="both", expand=True)

        # 侧边栏 — 明显的不同底色
        self.sidebar = ctk.CTkFrame(
            self.body, width=SIDEBAR_WIDTH,
            fg_color=("#E8E8E8", "#0D0D0D"), corner_radius=0,
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # 内容区
        self.content = ctk.CTkFrame(self.body, fg_color="transparent")
        self.content.pack(side="left", fill="both", expand=True)

    # ---- 侧边栏 ----

    def _build_sidebar(self):
        # Logo
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(fill="x", padx=16, pady=(24, 28))
        ctk.CTkLabel(
            logo_frame, text="PerfBoost",
            font=ctk.CTkFont(size=17, weight="bold"),
        ).pack(anchor="w")

        # 导航（用一个容器，剩余空间留空）
        nav_container = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        nav_container.pack(fill="both", expand=True, padx=0, pady=0)

        self._nav_frames: dict[str, ctk.CTkFrame] = {}
        self._nav_labels: dict[str, ctk.CTkLabel] = {}
        self._nav_indicators: dict[str, ctk.CTkFrame] = {}

        for i, (label, key) in enumerate(NAV_ITEMS):
            row = ctk.CTkFrame(
                nav_container,
                fg_color="transparent",
                corner_radius=8,
                height=38,
            )
            row.pack(fill="x", padx=10, pady=2)
            row.pack_propagate(False)
            self._nav_frames[key] = row

            dot = ctk.CTkFrame(row, width=8, height=8, corner_radius=4)
            dot.place(x=14, rely=0.5, anchor="w")

            lbl = ctk.CTkLabel(
                row, text=label,
                font=ctk.CTkFont(size=14),
                text_color=("#333333", "#AAAAAA"),
            )
            lbl.place(x=36, rely=0.5, anchor="w")

            # 绑定
            for w in (row, lbl):
                w.bind("<Button-1>", lambda e, k=key: self._navigate_to(k))
                w.bind("<Enter>", lambda e, r=row: r.configure(fg_color=("#D0D0D0", "#1A1A1A")))
                w.bind("<Leave>", lambda e, r=row, k=key: self._restore_row(r, k))

            self._nav_labels[key] = lbl

            def _make_hover(r, k):
                return lambda e: r.configure(fg_color=("#D0D0D0", "#1A1A1A"))
            dot.bind("<Enter>", _make_hover(row, key))

        # 底部（紧贴下边缘）
        bottom = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bottom.pack(side="bottom", fill="x", padx=0, pady=(0, 12))

        ctk.CTkFrame(
            bottom, height=1, fg_color=("#CCCCCC", "#222222"),
        ).pack(fill="x", padx=14, pady=(0, 8))

        # 品牌徽章：可点击跳转设置
        self.brand_badge = ctk.CTkFrame(
            bottom, corner_radius=6,
            fg_color=("#E0E0E0", "#1A1A1A"),
            cursor="hand2",
        )
        self.brand_badge.pack(anchor="w", padx=14)

        ctk.CTkLabel(
            self.brand_badge, text="⚡ PerfBoost",
            font=ctk.CTkFont(size=12),
            text_color=("#555555", "#BBBBBB"),
        ).pack(padx=10, pady=4)

        # 悬停效果
        self.brand_badge.bind("<Enter>", lambda e: self.brand_badge.configure(
            fg_color=("#D0D0D0", "#2A2A2A")))
        self.brand_badge.bind("<Leave>", lambda e: self.brand_badge.configure(
            fg_color=("#E0E0E0", "#1A1A1A")))
        # 点击跳转设置
        self.brand_badge.bind("<Button-1>", lambda e: self._navigate_to("settings"))

    def _restore_row(self, row, key):
        """还原行 hover 状态（保留选中高亮）."""
        active = getattr(self, "_active_key", None)
        if key == active:
            row.configure(fg_color=("#D6E4F0", "#152C40"))
        else:
            row.configure(fg_color="transparent")

    # ---- 页面 ----

    def _build_pages(self):
        self._pages: dict[str, ctk.CTkFrame] = {}
        self._pages["dashboard"] = DashboardFrame(self.content, self.config)
        self._pages["cleaner"] = CleanerFrame(self.content, self.config)
        self._pages["startup"] = StartupFrame(self.content, self.config)
        self._pages["process"] = ProcessFrame(self.content)
        self._pages["disk_analyzer"] = DiskAnalyzerFrame(self.content, self.config)
        self._pages["settings"] = SettingsFrame(
            self.content, self.config, on_theme_change=self._on_theme_changed,
        )

    def _navigate_to(self, key: str):
        self._active_key = key

        for page in self._pages.values():
            page.pack_forget()
        self._pages[key].pack(fill="both", expand=True)

        # 更新导航高亮
        for nav_key, row in self._nav_frames.items():
            lbl = self._nav_labels.get(nav_key)
            if nav_key == key:
                row.configure(fg_color=("#D6E4F0", "#152C40"))
                if lbl:
                    lbl.configure(text_color=("#1A5276", "#64B5F6"), font=ctk.CTkFont(size=14, weight="bold"))
            else:
                row.configure(fg_color="transparent")
                if lbl:
                    lbl.configure(text_color=("#333333", "#AAAAAA"), font=ctk.CTkFont(size=14))

    # ---- 监控 ----

    def _poll_monitor(self):
        try:
            data = self.monitor._sample()
            # 注入开机时间
            boot = get_boot_time()
            if boot:
                elapsed = time.time() - boot
                data["_boot_hours"] = int(elapsed // 3600)
                data["_boot_minutes"] = int((elapsed % 3600) // 60)
            self._pages["dashboard"].update_display(data)
            # 更新托盘图标状态
            try:
                self.tray.update_status(
                    data.get("cpu_percent", 0),
                    data.get("memory_percent", 0),
                )
            except Exception:
                pass
        except Exception:
            pass
        self.root.after(1000, self._poll_monitor)

    # ---- 窗口控制 ----

    def _on_theme_changed(self, theme: str):
        if theme == "system":
            theme = get_theme_from_registry()
        ctk.set_appearance_mode(theme)

    def _show_window(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def _hide_to_tray(self):
        self.root.withdraw()

    def _quit_app(self):
        self.monitor.stop()
        self.tray.stop()
        self.root.destroy()

    def run(self):
        try:
            self.tray.start()
        except Exception:
            pass
        self.root.mainloop()
