# PerfBoost UI 全面改版 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 PerfBoost 前端从 CTkTabview 布局改造为左侧导航栏 + 右侧内容区 + 底部状态栏的 Windows 11 现代风格

**Architecture:** app.py 作为主容器，左侧 CTkFrame 放导航按钮，右侧 CTkFrame 堆叠 5 个页面 Frame，导航切换通过 `pack_forget()` / `pack()` 控制显示。底部 status_bar 显示开机时间和版本号。

**Tech Stack:** Python 3.9+ / CustomTkinter / psutil

**设计文档:** `docs/superpowers/specs/2026-06-07-perfboost-ui-redesign.md`

---

### Task 1: app.py — 整体布局改造（左导航 + 右内容 + 底部状态栏）

**Files:**
- Modify: `app.py`

**设计要点:** 删除 CTkTabview，用 sidebar（左侧 160px 宽） + content_area（右侧自适应）替代。sidebar 放 5 个导航按钮，点击切换 content_area 中对应的 Frame。

- [ ] **Step 1: 重写 app.py 布局**

```python
"""主应用窗口：左侧导航栏 + 右侧内容区 + 底部状态栏."""

import time
import customtkinter as ctk

from core.monitor import SystemMonitor
from core.tray import SystemTray
from utils.config import Config
from utils.helpers import format_bytes, get_boot_time, get_theme_from_registry
from ui.dashboard import DashboardFrame
from ui.cleaner import CleanerFrame
from ui.startup import StartupFrame
from ui.process import ProcessFrame
from ui.settings import SettingsFrame


SIDEBAR_WIDTH = 160
STATUS_BAR_HEIGHT = 32
NAV_ITEMS = [
    ("📊 仪表盘", "dashboard"),
    ("🧹 清理", "cleaner"),
    ("🚀 启动项", "startup"),
    ("📋 进程", "process"),
    ("⚙️ 设置", "settings"),
]


class PerfBoostApp:
    def __init__(self):
        self.config = Config()
        self.monitor = SystemMonitor(interval=self.config.get("monitor_interval", 1))

        self._apply_theme()
        ctk.set_default_color_theme("blue")

        self.root = ctk.CTk()
        self.root.title("PerfBoost - 系统性能优化")
        self.root.geometry("820x620")
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
        self._build_statusbar()
        self._navigate_to("dashboard")

        self.monitor.start()
        self._poll_monitor()
        self.root.protocol("WM_DELETE_WINDOW", self._quit_app)

    def _apply_theme(self):
        theme = self.config.get("theme", "system")
        if theme == "system":
            theme = get_theme_from_registry()
        ctk.set_appearance_mode(theme)

    # ---- 布局骨架 ----

    def _build_layout(self):
        """创建主容器：sidebar + content + statusbar."""
        self.body = ctk.CTkFrame(self.root, fg_color="transparent")
        self.body.pack(fill="both", expand=True)

        self.sidebar = ctk.CTkFrame(self.body, width=SIDEBAR_WIDTH, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self.content = ctk.CTkFrame(self.body, fg_color="transparent")
        self.content.pack(side="left", fill="both", expand=True)

        self.statusbar = ctk.CTkFrame(self.root, height=STATUS_BAR_HEIGHT, corner_radius=0)
        self.statusbar.pack(side="bottom", fill="x")
        self.statusbar.pack_propagate(False)

    # ---- 侧边栏 ----

    def _build_sidebar(self):
        """Logo + 导航按钮."""
        # Logo 区域
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(fill="x", pady=(20, 10))
        ctk.CTkLabel(logo_frame, text="⚡", font=ctk.CTkFont(size=28)).pack()
        ctk.CTkLabel(logo_frame, text="PerfBoost", font=ctk.CTkFont(size=14, weight="bold")).pack()

        # 分隔线
        ctk.CTkFrame(self.sidebar, height=1, fg_color="gray30").pack(fill="x", padx=15, pady=(0, 10))

        # 导航按钮
        self._nav_buttons: dict[str, ctk.CTkButton] = {}
        for text, key in NAV_ITEMS:
            btn = ctk.CTkButton(
                self.sidebar, text=text, anchor="w",
                fg_color="transparent",
                hover_color="gray30",
                corner_radius=6,
                height=36,
                command=lambda k=key: self._navigate_to(k),
            )
            btn.pack(fill="x", padx=10, pady=3)
            self._nav_buttons[key] = btn

    # ---- 内容区页面 ----

    def _build_pages(self):
        """创建 5 个页面 Frame，堆叠在 content 中."""
        self._pages: dict[str, ctk.CTkFrame] = {}

        # 仪表盘
        self._pages["dashboard"] = DashboardFrame(self.content, self.config)
        # 清理
        self._pages["cleaner"] = CleanerFrame(self.content, self.config)
        # 启动项
        self._pages["startup"] = StartupFrame(self.content, self.config)
        # 进程
        self._pages["process"] = ProcessFrame(self.content)
        # 设置
        self._pages["settings"] = SettingsFrame(
            self.content, self.config, on_theme_change=self._on_theme_changed,
        )

    def _navigate_to(self, key: str):
        """切换到指定页面."""
        # 隐藏所有页面
        for page in self._pages.values():
            page.pack_forget()

        # 显示目标页面
        self._pages[key].pack(fill="both", expand=True)

        # 高亮对应的导航按钮
        for nav_key, btn in self._nav_buttons.items():
            if nav_key == key:
                btn.configure(fg_color="gray25")
            else:
                btn.configure(fg_color="transparent")

    # ---- 底部状态栏 ----

    def _build_statusbar(self):
        """开机时间 (左) + 版本号 (右)."""
        self.boot_label = ctk.CTkLabel(
            self.statusbar, text="", font=ctk.CTkFont(size=10),
            text_color="gray60",
        )
        self.boot_label.pack(side="left", padx=12, pady=4)

        ctk.CTkLabel(
            self.statusbar, text="v1.0", font=ctk.CTkFont(size=10),
            text_color="gray60",
        ).pack(side="right", padx=12, pady=4)

        self._update_boot_time()

    def _update_boot_time(self):
        """更新开机时间显示."""
        boot = get_boot_time()
        if boot:
            elapsed = time.time() - boot
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            self.boot_label.configure(text=f"💻 开机 {hours}h {minutes}m")
        else:
            self.boot_label.configure(text="")
        # 每分钟刷新一次
        self.root.after(60000, self._update_boot_time)

    # ---- 监控轮询 ----

    def _poll_monitor(self):
        """每 1 秒采样并更新仪表盘."""
        try:
            data = self.monitor._sample()
            self._pages["dashboard"].update_display(data)
        except Exception:
            pass
        self.root.after(1000, self._poll_monitor)

    # ---- 主题 / 窗口控制 ----

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
```

- [ ] **Step 2: 启动验证**

```bash
cd E:\Projects\perfboost && python main.py
```

预期：窗口出现，左侧导航栏可见，默认显示仪表盘，底部显示开机时间和 v1.0

- [ ] **Step 3: 提交**

```bash
git add app.py
git commit -m "feat: 整体布局改为左侧导航栏 + 右侧内容区 + 底部状态栏"
```

---

### Task 2: ui/dashboard.py — 4 卡片网格布局

**Files:**
- Modify: `ui/dashboard.py`

- [ ] **Step 1: 重写仪表盘为 2x2 卡片网格**

```python
"""仪表盘页面：4 张数据卡片 — CPU/内存/磁盘/网络."""

import customtkinter as ctk

from utils.helpers import format_bytes


class DashboardFrame(ctk.CTkFrame):
    def __init__(self, master, config, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.config = config
        self._build_ui()

    def _build_ui(self):
        # 页面标题
        ctk.CTkLabel(
            self, text="系统仪表盘",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(anchor="w", padx=20, pady=(15, 15))

        # 第一行：CPU + 内存
        row1 = ctk.CTkFrame(self, fg_color="transparent")
        row1.pack(fill="x", padx=15, pady=(0, 10))

        self._build_cpu_card(row1)
        self._build_memory_card(row1)

        # 第二行：磁盘 + 网络
        row2 = ctk.CTkFrame(self, fg_color="transparent")
        row2.pack(fill="x", padx=15, pady=(0, 10))

        self._build_disk_card(row2)
        self._build_network_card(row2)

    # ---- CPU 卡片 ----

    def _build_cpu_card(self, parent):
        card = ctk.CTkFrame(parent, corner_radius=10)
        card.pack(side="left", fill="both", expand=True, padx=(0, 5))

        ctk.CTkLabel(card, text="🖥 CPU", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=14, pady=(12, 6))

        self.cpu_label = ctk.CTkLabel(card, text="0%", font=ctk.CTkFont(size=36, weight="bold"))
        self.cpu_label.pack(anchor="w", padx=14)

        self.cpu_bar = ctk.CTkProgressBar(card, height=8, corner_radius=4)
        self.cpu_bar.pack(fill="x", padx=14, pady=(6, 4))
        self.cpu_bar.set(0)

        self.temp_label = ctk.CTkLabel(card, text="温度: --°C", font=ctk.CTkFont(size=11), text_color="gray60")
        self.temp_label.pack(anchor="w", padx=14, pady=(0, 12))

    # ---- 内存卡片 ----

    def _build_memory_card(self, parent):
        card = ctk.CTkFrame(parent, corner_radius=10)
        card.pack(side="right", fill="both", expand=True, padx=(5, 0))

        ctk.CTkLabel(card, text="🧠 内存", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=14, pady=(12, 6))

        self.mem_pct_label = ctk.CTkLabel(card, text="0%", font=ctk.CTkFont(size=36, weight="bold"))
        self.mem_pct_label.pack(anchor="w", padx=14)

        self.mem_detail_label = ctk.CTkLabel(card, text="0 / 0 GB", font=ctk.CTkFont(size=12), text_color="gray60")
        self.mem_detail_label.pack(anchor="w", padx=14, pady=(2, 6))

        self.mem_bar = ctk.CTkProgressBar(card, height=8, corner_radius=4)
        self.mem_bar.pack(fill="x", padx=14, pady=(0, 12))
        self.mem_bar.set(0)

    # ---- 磁盘卡片 ----

    def _build_disk_card(self, parent):
        card = ctk.CTkFrame(parent, corner_radius=10)
        card.pack(side="left", fill="both", expand=True, padx=(0, 5))

        ctk.CTkLabel(card, text="💾 磁盘", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=14, pady=(12, 6))

        self.disk_container = ctk.CTkFrame(card, fg_color="transparent")
        self.disk_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self._disk_widgets: list[dict] = []

    # ---- 网络卡片 ----

    def _build_network_card(self, parent):
        card = ctk.CTkFrame(parent, corner_radius=10)
        card.pack(side="right", fill="both", expand=True, padx=(5, 0))

        ctk.CTkLabel(card, text="🌐 网络", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=14, pady=(12, 6))

        self.net_upload_label = ctk.CTkLabel(card, text="↑ 0 B/s", font=ctk.CTkFont(size=18, weight="bold"))
        self.net_upload_label.pack(anchor="w", padx=14, pady=(10, 2))

        self.net_download_label = ctk.CTkLabel(card, text="↓ 0 B/s", font=ctk.CTkFont(size=18, weight="bold"))
        self.net_download_label.pack(anchor="w", padx=14, pady=(0, 12))

    # ---- 数据更新 ----

    def update_display(self, data: dict):
        """由 app.py 轮询调用."""
        cpu = data["cpu_percent"]
        self.cpu_label.configure(text=f"{cpu:.0f}%")
        self.cpu_bar.set(cpu / 100)

        temp = data.get("temperature")
        if temp is not None:
            self.temp_label.configure(text=f"温度: {temp:.0f}°C")
        else:
            self.temp_label.configure(text="温度: N/A")

        mem_pct = data["memory_percent"]
        self.mem_pct_label.configure(text=f"{mem_pct:.0f}%")
        self.mem_bar.set(mem_pct / 100)
        self.mem_detail_label.configure(
            text=f"{format_bytes(data['memory_used'])} / {format_bytes(data['memory_total'])}"
        )

        self._update_disks(data.get("disks", []))
        self._update_network(data.get("net_upload", 0), data.get("net_download", 0))

    def _update_disks(self, disks: list[dict]):
        # 首次创建磁盘行
        if not self._disk_widgets:
            for disk in disks:
                frame = ctk.CTkFrame(self.disk_container, fg_color="transparent")
                frame.pack(fill="x", pady=2)

                label = ctk.CTkLabel(frame, text="", width=36, anchor="w", font=ctk.CTkFont(size=12))
                label.pack(side="left")

                bar = ctk.CTkProgressBar(frame, height=6, corner_radius=3)
                bar.pack(side="left", fill="x", expand=True, padx=4)

                detail = ctk.CTkLabel(frame, text="", font=ctk.CTkFont(size=10))
                detail.pack(side="right")

                self._disk_widgets.append({"label": label, "bar": bar, "detail": detail})

        # 更新值
        for i, widget in enumerate(self._disk_widgets):
            if i < len(disks):
                d = disks[i]
                widget["label"].configure(text=f"{d['mountpoint']} ")
                widget["bar"].set(d["percent"] / 100)
                widget["detail"].configure(text=f"{format_bytes(d['used'])}/{format_bytes(d['total'])}")

    def _update_network(self, upload, download):
        self.net_upload_label.configure(text=f"↑ {format_bytes(int(upload))}/s")
        self.net_download_label.configure(text=f"↓ {format_bytes(int(download))}/s")
```

- [ ] **Step 2: 启动验证**

```bash
cd E:\Projects\perfboost && python main.py
```

预期：仪表盘显示 4 张卡片（CPU/内存一左一右，磁盘/网络一左一右），数据实时更新

- [ ] **Step 3: 提交**

```bash
git add ui/dashboard.py
git commit -m "feat: 仪表盘改为 4 卡片 2x2 网格布局"
```

---

### Task 3: ui/cleaner.py — 卡片式分类列表

**Files:**
- Modify: `ui/cleaner.py`

- [ ] **Step 1: 重写清理页面为卡片式**

```python
"""清理页面：卡片式分类列表."""

import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime

from core.cleaner import JunkCleaner
from utils.helpers import format_bytes
from utils.config import Config


class CleanerFrame(ctk.CTkFrame):
    def __init__(self, master, config: Config, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.config = config
        self.cleaner = JunkCleaner()
        self._categories = []
        self._checkboxes: dict[str, ctk.BooleanVar] = {}
        self._all_var = ctk.BooleanVar(value=True)
        self._build_ui()

    def _build_ui(self):
        # 标题
        ctk.CTkLabel(
            self, text="垃圾清理",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(anchor="w", padx=20, pady=(15, 10))

        # 按钮 + 全选
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", padx=20, pady=(0, 10))

        self.scan_btn = ctk.CTkButton(toolbar, text="🔍 扫描垃圾文件", command=self._on_scan)
        self.scan_btn.pack(side="left", padx=(0, 5))

        self.clean_btn = ctk.CTkButton(
            toolbar, text="🧹 一键清理", command=self._on_clean,
            state="disabled", fg_color="#c0392b", hover_color="#e74c3c",
        )
        self.clean_btn.pack(side="left", padx=5)

        self.select_all_cb = ctk.CTkCheckBox(
            toolbar, text="全选", variable=self._all_var,
            command=self._toggle_all,
        )
        self.select_all_cb.pack(side="right", padx=5)

        # 状态文字
        self.status_label = ctk.CTkLabel(
            self, text="就绪 — 点击扫描开始",
            font=ctk.CTkFont(size=11), text_color="gray60",
        )
        self.status_label.pack(anchor="w", padx=20, pady=(0, 5))

        # 分类卡片容器
        self.cat_container = ctk.CTkScrollableFrame(self)
        self.cat_container.pack(fill="both", expand=True, padx=15, pady=(0, 10))

    def _toggle_all(self):
        state = self._all_var.get()
        for var in self._checkboxes.values():
            var.set(state)

    def _on_scan(self):
        self.scan_btn.configure(state="disabled", text="扫描中...")
        self.status_label.configure(text="正在扫描...")
        self.update_idletasks()

        try:
            self._categories = self.cleaner.scan()
            self._render_categories()
            total = sum(c.total_size for c in self._categories)
            self.status_label.configure(text=f"✅ 扫描完成，共可清理 {format_bytes(total)}")
        except Exception as e:
            self.status_label.configure(text=f"扫描出错: {e}")
        finally:
            self.scan_btn.configure(state="normal", text="🔍 重新扫描")
            self.clean_btn.configure(state="normal")

    def _render_categories(self):
        for w in self.cat_container.winfo_children():
            w.destroy()
        self._checkboxes.clear()

        saved = self.config.get("clean_categories", {})
        max_size = max((c.total_size for c in self._categories), default=1)

        for cat in self._categories:
            card = ctk.CTkFrame(self.cat_container, corner_radius=8)
            card.pack(fill="x", pady=3)

            # 第一行：名称 + 大小 + 复选框
            row1 = ctk.CTkFrame(card, fg_color="transparent")
            row1.pack(fill="x", padx=10, pady=(8, 4))

            default_checked = saved.get(cat.key, True)
            var = ctk.BooleanVar(value=default_checked)
            cb = ctk.CTkCheckBox(row1, text=cat.label, variable=var)
            cb.pack(side="left")
            self._checkboxes[cat.key] = var

            size_text = format_bytes(cat.total_size)
            ctk.CTkLabel(row1, text=size_text, width=80, font=ctk.CTkFont(size=12, weight="bold")).pack(side="right")

            if cat.needs_admin:
                ctk.CTkLabel(row1, text="🔒", font=ctk.CTkFont(size=10)).pack(side="right", padx=(0, 4))

            # 第二行：进度条 + 预览
            row2 = ctk.CTkFrame(card, fg_color="transparent")
            row2.pack(fill="x", padx=10, pady=(0, 8))

            bar = ctk.CTkProgressBar(row2, height=6, corner_radius=3)
            bar.pack(side="left", fill="x", expand=True)
            bar.set(cat.total_size / max_size if max_size > 0 else 0)

            if cat.files and cat.key != "recycle_bin":
                ctk.CTkLabel(row2, text=f"{len(cat.files)} 个文件", font=ctk.CTkFont(size=10), text_color="gray60").pack(side="left", padx=(8, 0))
                ctk.CTkButton(
                    row2, text="👁 预览", width=50, height=22,
                    font=ctk.CTkFont(size=10),
                    command=lambda c=cat: self._on_preview(c),
                ).pack(side="right")

    def _on_preview(self, cat):
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"预览 — {cat.label}")
        dialog.geometry("500x400")
        dialog.grab_set()

        ctk.CTkLabel(dialog, text=f"{cat.label} — 共 {len(cat.files)} 项",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 10))

        scroll = ctk.CTkScrollableFrame(dialog, width=460, height=300)
        scroll.pack(fill="both", expand=True, padx=15, pady=10)

        for fpath, fsize in cat.files[:200]:
            row = ctk.CTkFrame(scroll, fg_color="transparent")
            row.pack(fill="x", pady=1)
            display_name = fpath.rsplit("\\", 1)[-1] if "\\" in fpath else fpath
            ctk.CTkLabel(row, text=display_name, anchor="w",
                         font=ctk.CTkFont(size=11)).pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(row, text=format_bytes(fsize),
                         font=ctk.CTkFont(size=11)).pack(side="right")

        ctk.CTkButton(dialog, text="关闭", command=dialog.destroy).pack(pady=10)

    def _on_clean(self):
        selected = {key for key, var in self._checkboxes.items() if var.get()}
        if not selected:
            self.status_label.configure(text="请至少选择一项")
            return

        total_size = sum(c.total_size for c in self._categories if c.key in selected)
        cat_names = [c.label for c in self._categories if c.key in selected]
        msg = "即将清理以下类别：\n\n" + "\n".join(f"• {n}" for n in cat_names)
        msg += f"\n\n预计释放空间：{format_bytes(total_size)}"
        msg += "\n\n确定继续？"

        if not messagebox.askyesno("确认清理", msg, parent=self):
            return

        self.clean_btn.configure(state="disabled", text="清理中...")
        self.status_label.configure(text="正在清理...")
        self.update_idletasks()

        try:
            freed, deleted, failed = self.cleaner.clean(selected)

            total_cleaned = self.config.get("total_cleaned_bytes", 0) + freed
            self.config.set("total_cleaned_bytes", total_cleaned)
            self.config.set("last_optimization", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

            result_msg = f"✅ 已释放: {format_bytes(freed)}"
            if failed:
                result_msg += "\n\n⚠ 以下文件无法删除：\n"
                for f in failed[:5]:
                    result_msg += f"• {f}\n"
                if len(failed) > 5:
                    result_msg += f"…共 {len(failed)} 项\n"
                result_msg += "\n建议：关闭相关程序后重试"
            messagebox.showinfo("清理结果", result_msg, parent=self)
            self.status_label.configure(text=f"✅ 清理完成！释放 {format_bytes(freed)}")
        except Exception as e:
            messagebox.showerror("清理出错", str(e), parent=self)
            self.status_label.configure(text=f"清理出错: {e}")
        finally:
            self.clean_btn.configure(state="normal", text="🧹 一键清理")
            self._on_scan()
```

- [ ] **Step 2: 启动验证**

```bash
cd E:\Projects\perfboost && python main.py
```

预期：清理页面，每类一张卡片，有进度条和预览按钮，全选复选框可用

- [ ] **Step 3: 提交**

```bash
git add ui/cleaner.py
git commit -m "feat: 清理页面改为卡片式分类列表，新增全选功能"
```

---

### Task 4: ui/startup.py — 卡片式行 + 影响评估图标

**Files:**
- Modify: `ui/startup.py`

- [ ] **Step 1: 重写启动项页面**

```python
"""启动项管理页面：卡片式行 + 影响评估."""

import customtkinter as ctk
from tkinter import messagebox

from core.startup import StartupManager, StartupEntry
from utils.config import Config


class StartupFrame(ctk.CTkFrame):
    def __init__(self, master, config: Config, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.config = config
        self.manager = StartupManager()
        self._entries: list[StartupEntry] = []
        self._switches: dict[int, ctk.CTkSwitch] = {}
        self._build_ui()
        self._refresh()

    def _build_ui(self):
        ctk.CTkLabel(
            self, text="启动项管理",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(anchor="w", padx=20, pady=(15, 10))

        # 工具栏
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", padx=20, pady=(0, 5))

        ctk.CTkButton(toolbar, text="🔄 刷新", command=self._refresh).pack(side="left", padx=(0, 5))
        ctk.CTkButton(toolbar, text="📋 已禁用列表", command=self._show_backups).pack(side="left")

        # 汇总
        self.summary_label = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(size=11), text_color="gray60",
        )
        self.summary_label.pack(anchor="w", padx=20, pady=(0, 5))

        # 列表
        self.list_frame = ctk.CTkScrollableFrame(self)
        self.list_frame.pack(fill="both", expand=True, padx=15, pady=(0, 10))

    def _refresh(self):
        for w in self.list_frame.winfo_children():
            w.destroy()
        self._switches.clear()

        try:
            self._entries = self.manager.get_entries()
            disabled_list = self.config.get("startup_disabled", [])

            enabled_count = 0
            for i, entry in enumerate(self._entries):
                card = ctk.CTkFrame(self.list_frame, corner_radius=8)
                card.pack(fill="x", pady=2)

                top_row = ctk.CTkFrame(card, fg_color="transparent")
                top_row.pack(fill="x", padx=10, pady=(8, 2))

                # 名称 + 来源
                ctk.CTkLabel(top_row, text=entry.name, width=140, anchor="w",
                             font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")
                ctk.CTkLabel(top_row, text=entry.source, width=60,
                             font=ctk.CTkFont(size=10), text_color="gray60").pack(side="left")

                is_enabled = entry.command not in disabled_list
                if is_enabled:
                    enabled_count += 1
                    status_text = "● 已启用"
                    status_color = "#27ae60"
                else:
                    status_text = "○ 已禁用"
                    status_color = "gray60"
                ctk.CTkLabel(top_row, text=status_text, width=60,
                             font=ctk.CTkFont(size=10), text_color=status_color).pack(side="right")

                # 开关
                switch = ctk.CTkSwitch(
                    top_row, text="",
                    command=lambda e=entry, idx=i: self._toggle(idx),
                    width=40,
                )
                if is_enabled:
                    switch.select()
                else:
                    switch.deselect()
                switch.pack(side="right", padx=(0, 5))
                self._switches[i] = switch

                # 底部行：命令路径
                bottom_row = ctk.CTkFrame(card, fg_color="transparent")
                bottom_row.pack(fill="x", padx=10, pady=(0, 4))

                cmd = entry.command
                if len(cmd) > 55:
                    cmd = cmd[:52] + "..."
                ctk.CTkLabel(bottom_row, text=cmd, font=ctk.CTkFont(size=10),
                             text_color="gray60").pack(side="left")

                # 影响评估
                impact = self.manager.get_impact_estimate(entry)
                icon = "❌" if "不存在" in impact else "⚠"
                ctk.CTkLabel(bottom_row, text=f"{icon} {impact}",
                             font=ctk.CTkFont(size=9),
                             text_color="#e74c3c" if "不存在" in impact else "gray60").pack(side="right")

            self.summary_label.configure(
                text=f"共 {len(self._entries)} 个启动项，{enabled_count} 个已启用"
            )
        except Exception as e:
            ctk.CTkLabel(self.list_frame, text=f"加载失败: {e}").pack()

    def _toggle(self, index: int):
        entry = self._entries[index]
        switch = self._switches[index]
        disabled = self.config.get("startup_disabled", [])

        if switch.get():
            self.manager.restore_entry(entry)
            if entry.command in disabled:
                disabled.remove(entry.command)
        else:
            impact = self.manager.get_impact_estimate(entry)
            if not messagebox.askyesno("确认禁用",
                                       f"确定禁用 \"{entry.name}\" 吗？\n{impact}",
                                       parent=self):
                switch.select()
                return
            self.manager.disable_entry(entry)
            if entry.command not in disabled:
                disabled.append(entry.command)

        self.config.set("startup_disabled", disabled)
        self._refresh()

    def _show_backups(self):
        backups = self.manager.get_backups()
        if not backups:
            messagebox.showinfo("已禁用列表", "暂无已禁用的启动项", parent=self)
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title("已禁用的启动项")
        dialog.geometry("500x350")
        dialog.grab_set()

        ctk.CTkLabel(dialog, text=f"共 {len(backups)} 项已禁用",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(15, 10))

        scroll = ctk.CTkScrollableFrame(dialog, width=460, height=220)
        scroll.pack(fill="both", expand=True, padx=15, pady=5)

        for entry in backups:
            row = ctk.CTkFrame(scroll, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=entry.name, width=120, anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(row, text=entry.source, width=100,
                         font=ctk.CTkFont(size=10)).pack(side="left", padx=2)
            ctk.CTkButton(
                row, text="恢复", width=50, height=24,
                font=ctk.CTkFont(size=11),
                command=lambda e=entry: self._restore_and_refresh(e, dialog),
            ).pack(side="right", padx=5)

        ctk.CTkButton(dialog, text="关闭", command=dialog.destroy).pack(pady=10)

    def _restore_and_refresh(self, entry: StartupEntry, dialog: ctk.CTkToplevel):
        if self.manager.restore_entry(entry):
            disabled = self.config.get("startup_disabled", [])
            if entry.command in disabled:
                disabled.remove(entry.command)
                self.config.set("startup_disabled", disabled)
            dialog.destroy()
            self._refresh()
            messagebox.showinfo("恢复成功", f"\"{entry.name}\" 已恢复启动", parent=self)
        else:
            messagebox.showerror("恢复失败", f"无法恢复 \"{entry.name}\"", parent=self)
```

- [ ] **Step 2: 启动验证**

```bash
cd E:\Projects\perfboost && python main.py
```

预期：启动项列表每行一张卡片，显示名称/来源/路径/影响评估/开关，底部有总数统计

- [ ] **Step 3: 提交**

```bash
git add ui/startup.py
git commit -m "feat: 启动项页面改为卡片式行，影响评估图标化"
```

---

### Task 5: ui/process.py — 内存可视化条 + 受保护标记

**Files:**
- Modify: `ui/process.py`

- [ ] **Step 1: 重写进程页面**

```python
"""进程管理页面：内存可视化条 + 受保护标记."""

import os
import subprocess
import customtkinter as ctk
from tkinter import Menu, messagebox

from core.process import ProcessManager


HEADER_COLS = [("名称", 140), ("PID", 60), ("CPU%", 55), ("内存", 100), ("", 30)]


class ProcessFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.manager = ProcessManager()
        self._procs: list[dict] = []
        self._selected_pid = None
        self._selected_name = ""
        self._selected_row = None
        self._build_ui()
        self._refresh()

    def _build_ui(self):
        ctk.CTkLabel(
            self, text="进程管理",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(anchor="w", padx=20, pady=(15, 10))

        # 工具栏
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", padx=20, pady=(0, 5))

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._filter())
        ctk.CTkEntry(toolbar, placeholder_text="搜索进程名...",
                     textvariable=self.search_var, width=180).pack(side="left", padx=(0, 5))

        ctk.CTkButton(toolbar, text="🔄 刷新", width=70, command=self._refresh).pack(side="left", padx=5)

        self.kill_btn = ctk.CTkButton(
            toolbar, text="❌ 结束进程", width=90,
            fg_color="#c0392b", hover_color="#e74c3c",
            state="disabled", command=self._kill_confirm,
        )
        self.kill_btn.pack(side="left", padx=5)

        # 列标题
        header = ctk.CTkFrame(self, fg_color="gray20")
        header.pack(fill="x", padx=15, pady=(5, 0))
        for text, width in HEADER_COLS:
            ctk.CTkLabel(header, text=text, width=width,
                         font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=2)

        # 列表
        self.list_frame = ctk.CTkScrollableFrame(self)
        self.list_frame.pack(fill="both", expand=True, padx=15, pady=(0, 0))

        # 底部状态
        self.status_label = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(size=11), text_color="gray60",
        )
        self.status_label.pack(anchor="w", padx=20, pady=(2, 10))

    def _refresh(self):
        self._selected_pid = None
        self._selected_name = ""
        self._selected_row = None
        self.kill_btn.configure(state="disabled")
        self._procs = self.manager.get_processes()
        self._render(self._procs)

    def _filter(self):
        query = self.search_var.get().lower()
        if not query:
            self._render(self._procs)
            return
        self._render([p for p in self._procs if query in p["name"].lower()])

    def _render(self, procs: list[dict]):
        for w in self.list_frame.winfo_children():
            w.destroy()
        self._selected_row = None

        max_mem = max((p["memory_mb"] for p in procs), default=1)

        for proc in procs[:100]:
            row = ctk.CTkFrame(self.list_frame, fg_color="transparent")
            row.pack(fill="x", pady=1)

            pid = proc["pid"]
            pname = proc["name"]
            is_protected = self.manager.is_protected(pid)

            ctk.CTkLabel(row, text=pname, width=140, anchor="w").pack(side="left", padx=2)
            ctk.CTkLabel(row, text=str(pid), width=60).pack(side="left", padx=2)
            ctk.CTkLabel(row, text=f"{proc['cpu_percent']:.1f}", width=55).pack(side="left", padx=2)

            # 内存列：文字 + 小进度条
            mem_frame = ctk.CTkFrame(row, fg_color="transparent", width=100)
            mem_frame.pack(side="left", padx=2)
            mem_text = f"{proc['memory_mb']:.0f} MB"
            ctk.CTkLabel(mem_frame, text=mem_text, width=60, anchor="w",
                         font=ctk.CTkFont(size=11)).pack(side="left")
            mem_bar = ctk.CTkProgressBar(mem_frame, width=35, height=4, corner_radius=2,
                                         progress_color="#27ae60")
            mem_bar.pack(side="left", padx=2)
            mem_bar.set(proc["memory_mb"] / max_mem if max_mem > 0 else 0)

            # 操作列
            if is_protected:
                ctk.CTkLabel(row, text="🔒", width=30,
                             font=ctk.CTkFont(size=11)).pack(side="left")
            else:
                ctk.CTkLabel(row, text="▶", width=30,
                             font=ctk.CTkFont(size=11), text_color="gray60").pack(side="left")

            # 绑定点击选中
            for child in row.winfo_children():
                child.bind("<Button-1>", lambda e, r=row, p=pid, n=pname: self._select_row(r, p, n))
            row.bind("<Button-1>", lambda e, r=row, p=pid, n=pname: self._select_row(r, p, n))

            # 右键菜单
            row.bind("<Button-3>", lambda e, p=pid, n=pname: self._context_menu(e, p, n))
            for child in row.winfo_children():
                child.bind("<Button-3>", lambda e, p=pid, n=pname: self._context_menu(e, p, n))

        self.status_label.configure(text=f"共 {len(procs)} 个进程")

    def _select_row(self, row, pid, name):
        if self._selected_row:
            self._selected_row.configure(fg_color="transparent")
        row.configure(fg_color="#2a5f8a")
        self._selected_row = row
        self._selected_pid = pid
        self._selected_name = name
        is_protected = self.manager.is_protected(pid)
        self.kill_btn.configure(state="disabled" if is_protected else "normal")
        self.status_label.configure(text=f"共 {len(self._procs)} 个进程 | 选中: {name} (PID: {pid})")

    def _context_menu(self, event, pid, name):
        self._select_row_by_pid(pid)
        menu = Menu(self, tearoff=0)
        menu.add_command(label=f"结束 {name}", command=lambda: self._kill_confirm())
        menu.add_command(label="打开文件位置", command=lambda: self._open_file_location(pid))
        menu.post(event.x_root, event.y_root)

    def _select_row_by_pid(self, pid):
        for child in self.list_frame.winfo_children():
            labels = [w for w in child.winfo_children() if isinstance(w, ctk.CTkLabel)]
            for label in labels:
                if label.cget("text") == str(pid):
                    pname = labels[0].cget("text")
                    self._select_row(child, pid, pname)
                    return

    def _kill_confirm(self):
        if not self._selected_pid:
            return
        if self.manager.is_protected(self._selected_pid):
            messagebox.showwarning("受保护", "这是系统关键进程，无法终止", parent=self)
            return
        if messagebox.askyesno("确认结束进程",
                               f"确定要终止 \"{self._selected_name}\" (PID: {self._selected_pid}) 吗？",
                               parent=self):
            if self.manager.kill_process(self._selected_pid):
                messagebox.showinfo("成功", f"进程 {self._selected_name} 已终止", parent=self)
            else:
                messagebox.showerror("失败", "无法终止进程（可能需要管理员权限）", parent=self)
            self._refresh()

    def _open_file_location(self, pid):
        try:
            import psutil
            proc = psutil.Process(pid)
            exe_path = proc.exe()
            if exe_path and os.path.exists(exe_path):
                subprocess.Popen(["explorer", "/select,", exe_path])
            else:
                messagebox.showinfo("提示", "无法获取该进程的文件路径", parent=self)
        except Exception as e:
            messagebox.showerror("错误", f"无法打开: {e}", parent=self)
```

- [ ] **Step 2: 启动验证**

```bash
cd E:\Projects\perfboost && python main.py
```

预期：进程列表每行有内存可视化条，🔒 标记受保护进程，底部显示进程总数和选中信息

- [ ] **Step 3: 提交**

```bash
git add ui/process.py
git commit -m "feat: 进程页面新增内存可视化条、受保护标记、选中统计"
```

---

### Task 6: ui/settings.py — 卡片分组 + 关于

**Files:**
- Modify: `ui/settings.py`

- [ ] **Step 1: 重写设置页面**

```python
"""设置页面：外观 + 关于."""

import customtkinter as ctk

from utils.config import Config


class SettingsFrame(ctk.CTkFrame):
    def __init__(self, master, config: Config, on_theme_change=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.config = config
        self._on_theme_change = on_theme_change
        self._build_ui()

    def _build_ui(self):
        ctk.CTkLabel(
            self, text="设置",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(anchor="w", padx=20, pady=(15, 15))

        # ---- 外观 ----
        appearance_card = ctk.CTkFrame(self, corner_radius=10)
        appearance_card.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(appearance_card, text="外观",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=14, pady=(12, 8))

        current_theme = self.config.get("theme", "system")
        self.theme_var = ctk.StringVar(value=current_theme)

        radio_frame = ctk.CTkFrame(appearance_card, fg_color="transparent")
        radio_frame.pack(fill="x", padx=14, pady=(0, 12))

        for value, label in [("system", "跟随系统"), ("dark", "暗色"), ("light", "亮色")]:
            ctk.CTkRadioButton(
                radio_frame, text=label, variable=self.theme_var, value=value,
                command=self._on_theme_changed,
            ).pack(side="left", padx=(0, 20), pady=4)

        # ---- 关于 ----
        about_card = ctk.CTkFrame(self, corner_radius=10)
        about_card.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(about_card, text="关于",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=14, pady=(12, 8))

        ctk.CTkLabel(about_card, text="PerfBoost  v1.0",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=14)
        ctk.CTkLabel(about_card, text="Windows 系统性能优化工具",
                     font=ctk.CTkFont(size=12), text_color="gray60").pack(anchor="w", padx=14, pady=(2, 12))

    def _on_theme_changed(self):
        theme = self.theme_var.get()
        self.config.set("theme", theme)
        if self._on_theme_change:
            self._on_theme_change(theme)
```

- [ ] **Step 2: 启动验证**

```bash
cd E:\Projects\perfboost && python main.py
```

预期：设置页面两个卡片——外观（主题三选一）和关于（版本信息）

- [ ] **Step 3: 提交**

```bash
git add ui/settings.py
git commit -m "feat: 设置页面改为卡片分组，新增关于区块"
```

---

## 验证清单

全部完成后运行：

```bash
cd E:\Projects\perfboost && python main.py
```

逐项检查：
1. [ ] 左侧导航栏 5 个按钮，点击切换右侧页面
2. [ ] 底部状态栏显示开机时间和 v1.0
3. [ ] 仪表盘 4 张卡片，数据实时刷新
4. [ ] 清理页面扫描正常，卡片式分类，全选可用
5. [ ] 启动项卡片式行，影响评估图标可见
6. [ ] 进程内存条可视化，🔒 标记受保护进程，选中高亮
7. [ ] 设置页面外观切换即时生效，关于信息显示
