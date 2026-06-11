"""磁盘分析页面 — Treemap 可视化目录大小分布."""

import os
import threading
import customtkinter as ctk
import tkinter as tk

from core.disk_analyzer import DiskScanner, FileEntry
from utils.helpers import format_bytes


class DiskAnalyzerFrame(ctk.CTkFrame):
    """磁盘分析页面：工具栏 + Canvas Treemap + 底部状态栏."""

    MIN_RECT_SIZE = 2        # 最小矩形边长（像素）
    MERGE_RATIO = 0.001      # 占比 < 0.1% 合并
    MAX_ITEMS = 200          # 超过此数量则合并最小的 10%
    PADDING = 1              # 矩形间距

    def __init__(self, master, config, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.config = config
        self._scanner = DiskScanner()
        self._root_path = ""
        self._entries: list[FileEntry] = []
        self._hovered_rect: int | None = None      # 当前悬停的 Canvas 矩形 id
        self._rect_map: dict[int, FileEntry] = {}  # canvas_id -> FileEntry
        self._breadcrumb_parts: list[str] = []     # 面包屑路径段
        self._scanning = False

        self._build_ui()

        # 页面首次加载时自动扫描用户主目录
        home = os.path.expanduser("~")
        if os.path.isdir(home):
            self.path_entry.insert(0, home)
            self._start_scan(home)

    # ===== 构建 UI =====

    def _build_ui(self):
        # 标题
        ctk.CTkLabel(
            self, text="磁盘分析",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(anchor="w", padx=20, pady=(15, 10))

        # 工具栏
        self._build_toolbar()

        # Canvas 区域
        self._build_canvas()

        # 底部状态栏
        self._build_statusbar()

    def _build_toolbar(self):
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", padx=15, pady=(0, 6))

        # 🏠 回到根目录
        self.home_btn = ctk.CTkButton(
            toolbar, text="🏠", width=36,
            command=self._on_go_home,
        )
        self.home_btn.pack(side="left", padx=(0, 4))

        # 路径输入框
        self.path_entry = ctk.CTkEntry(toolbar, placeholder_text="选择或输入目录路径...")
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.path_entry.bind("<Return>", lambda e: self._on_scan())

        # 浏览按钮
        self.browse_btn = ctk.CTkButton(
            toolbar, text="浏览...", width=70,
            command=self._on_browse,
        )
        self.browse_btn.pack(side="left", padx=(0, 4))

        # 扫描按钮
        self.scan_btn = ctk.CTkButton(
            toolbar, text="扫描", width=60,
            command=self._on_scan,
        )
        self.scan_btn.pack(side="left")

        # 面包屑行（内容由 _draw_breadcrumb 动态填充）
        self.breadcrumb_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.breadcrumb_frame.pack(fill="x", padx=15, pady=(0, 4))

    def _build_canvas(self):
        """创建 Treemap 绘制画布."""
        canvas_frame = ctk.CTkFrame(self, corner_radius=8)
        canvas_frame.pack(fill="both", expand=True, padx=15, pady=(0, 6))

        self.canvas = tk.Canvas(
            canvas_frame,
            bg=self._canvas_bg(),
            highlightthickness=0,
            bd=0,
        )
        self.canvas.pack(fill="both", expand=True, padx=2, pady=2)

        # 绑定事件
        self.canvas.bind("<Motion>", self._on_mouse_move)
        self.canvas.bind("<Leave>", self._on_canvas_leave)
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.bind("<Configure>", self._on_canvas_resize)

    def _build_statusbar(self):
        status = ctk.CTkFrame(self, fg_color=("#E8E8E8", "#1A1A1A"), corner_radius=8)
        status.pack(fill="x", padx=15, pady=(0, 10))

        self.status_label = ctk.CTkLabel(
            status, text="📊 选择一个目录开始扫描",
            font=ctk.CTkFont(size=12), text_color=("#555555", "#888888"),
        )
        self.status_label.pack(padx=14, pady=8)

    # ===== 主题适配 =====

    def _canvas_bg(self) -> str:
        """根据当前主题返回 Canvas 背景色."""
        try:
            mode = ctk.get_appearance_mode()
        except Exception:
            mode = "Dark"
        return "#2B2B2B" if mode == "Dark" else "#F5F5F5"

    def _text_color(self) -> str:
        """根据当前主题返回 Canvas 文字颜色."""
        try:
            mode = ctk.get_appearance_mode()
        except Exception:
            mode = "Dark"
        return "#E0E0E0" if mode == "Dark" else "#222222"

    # ===== 交互事件 =====

    def _on_browse(self):
        """弹出文件夹选择对话框."""
        from tkinter import filedialog
        path = filedialog.askdirectory(title="选择要分析的目录")
        if path:
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, path)
            self._start_scan(path)

    def _on_scan(self):
        """点击扫描按钮."""
        path = self.path_entry.get().strip()
        if not path:
            return
        if not os.path.isdir(path):
            self.status_label.configure(text="⚠️ 路径不存在或不是目录")
            return
        self._start_scan(path)

    def _on_go_home(self):
        """回到最初选择的根目录."""
        if self._root_path and os.path.isdir(self._root_path):
            self._start_scan(self._root_path)

    def _on_breadcrumb_click(self, index: int):
        """点击面包屑某一段，跳转到对应层级的目录."""
        parts = self._build_breadcrumb(
            self._entries[0].path if self._entries else self._root_path
        )
        if 0 <= index < len(parts):
            self._start_scan(parts[index])

    def _on_mouse_move(self, event):
        """鼠标移动 — 检测矩形悬停."""
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        overlapping = self.canvas.find_overlapping(x, y, x, y)

        new_hovered = None
        for item_id in reversed(overlapping):
            if item_id in self._rect_map:  # 只关心矩形，不关心文字
                new_hovered = item_id
                break

        # 还原之前悬停的矩形
        if self._hovered_rect and self._hovered_rect != new_hovered:
            self._draw_rect_normal(self._hovered_rect)

        # 高亮新矩形
        if new_hovered and new_hovered != self._hovered_rect:
            self._draw_rect_hovered(new_hovered)
            entry = self._rect_map.get(new_hovered)
            if entry:
                type_icon = "📁" if entry.is_dir else "📄"
                self.status_label.configure(
                    text=f"{type_icon} {entry.path}   |   {format_bytes(entry.size)}"
                )

        self._hovered_rect = new_hovered

    def _on_canvas_leave(self, _event):
        """鼠标离开 Canvas — 清除悬停状态."""
        if self._hovered_rect:
            self._draw_rect_normal(self._hovered_rect)
            self._hovered_rect = None
            self._update_count_status()

    def _on_canvas_click(self, event):
        """点击矩形 — 进入子目录."""
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        overlapping = self.canvas.find_overlapping(x, y, x, y)

        for item_id in reversed(overlapping):
            entry = self._rect_map.get(item_id)
            if entry and entry.is_dir:
                self._start_scan(entry.path)
                return

    def _on_canvas_resize(self, _event):
        """Canvas 大小变化时重绘."""
        if self._entries:
            self._draw_treemap()

    # ===== 扫描 =====

    def _start_scan(self, path: str):
        """启动后台扫描线程."""
        if self._scanning:
            return
        self._scanning = True
        self._root_path = path
        self._entries = []
        self.scan_btn.configure(text="扫描中...", state="disabled")
        self.browse_btn.configure(state="disabled")
        self.status_label.configure(text="🔍 正在扫描...")

        thread = threading.Thread(target=self._scan_worker, args=(path,), daemon=True)
        thread.start()

    def _scan_worker(self, path: str):
        """后台线程：执行扫描，完成后在主线程绘制."""
        entries = self._scanner.scan(path)
        # 合并过小项 + 限制数量
        entries = self._merge_small(entries)
        self._entries = entries
        self._breadcrumb_parts = self._build_breadcrumb(path)
        # 回到主线程更新 UI
        self.after(0, self._on_scan_done)

    def _on_scan_done(self):
        """扫描完成回调（主线程）."""
        self._scanning = False
        self.scan_btn.configure(text="扫描", state="normal")
        self.browse_btn.configure(state="normal")
        self._draw_treemap()
        self._draw_breadcrumb()
        self._update_count_status()

    def _merge_small(self, entries: list[FileEntry]) -> list[FileEntry]:
        """合并过小项到"其他"类别."""
        if not entries:
            return entries
        total = sum(e.size for e in entries)
        if total == 0:
            return entries

        # 限制数量：超过 MAX_ITEMS 则截断
        if len(entries) > self.MAX_ITEMS:
            entries = entries[:self.MAX_ITEMS]

        # 过滤占比 < 0.1% 的项
        threshold = total * self.MERGE_RATIO
        kept = []
        other_size = 0
        for e in entries:
            if e.size >= threshold:
                kept.append(e)
            else:
                other_size += e.size

        if other_size > 0:
            parent_dir = os.path.dirname(kept[0].path) if kept else ""
            kept.append(FileEntry(
                name=f"其他 ({len(entries) - len(kept) + 1} 项)",
                path=os.path.join(parent_dir, "(其他)"),
                size=other_size,
                is_dir=False,
            ))
            kept.sort(key=lambda e: e.size, reverse=True)

        return kept

    def _build_breadcrumb(self, path: str) -> list[str]:
        """构建面包屑路径段列表."""
        parts = []
        current = path.rstrip("\\")
        while current:
            parts.insert(0, current)
            parent = os.path.dirname(current)
            if parent == current:
                break
            current = parent
        return parts

    # ===== 绘制 =====

    def _draw_treemap(self):
        """清空 Canvas 并重绘 Treemap."""
        self.canvas.delete("all")
        self._rect_map.clear()

        if not self._entries:
            self.canvas.create_text(
                self.canvas.winfo_width() // 2 if self.canvas.winfo_width() > 1 else 200,
                self.canvas.winfo_height() // 2 if self.canvas.winfo_height() > 1 else 150,
                text="没有可显示的项目", fill=self._text_color(),
                font=("Microsoft YaHei", 14),
            )
            return

        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 10 or h < 10:
            return

        # 用 squarify 计算矩形布局
        import squarify
        sizes = [max(e.size, 1) for e in self._entries]
        normalized = squarify.normalize_sizes(sizes, w, h)
        rects = squarify.squarify(normalized, 0, 0, w, h)

        # 绘制矩形
        for i, rect in enumerate(rects):
            if i >= len(self._entries):
                break
            entry = self._entries[i]
            x1, y1, dx, dy = rect["x"], rect["y"], rect["dx"], rect["dy"]
            x2, y2 = x1 + dx, y1 + dy

            # 留间距
            if dx > self.PADDING * 2 and dy > self.PADDING * 2:
                rx1, ry1 = x1 + self.PADDING, y1 + self.PADDING
                rx2, ry2 = x2 - self.PADDING, y2 - self.PADDING
            else:
                rx1, ry1, rx2, ry2 = x1, y1, x2, y2

            color = self._rect_color(entry, i)
            rect_id = self.canvas.create_rectangle(
                rx1, ry1, rx2, ry2,
                fill=color, outline="", width=0,
            )
            self._rect_map[rect_id] = entry

            # 绘制文件名和大小（矩形太小则跳过）
            rw, rh = rx2 - rx1, ry2 - ry1
            if rw > 30 and rh > 20:
                font_size = max(9, min(14, int(min(rw, rh) / 8)))
                name = entry.name if len(entry.name) < 30 else entry.name[:28] + ".."
                size_text = format_bytes(entry.size)
                label = f"{name}\n{size_text}"
                self.canvas.create_text(
                    (rx1 + rx2) // 2, (ry1 + ry2) // 2,
                    text=label,
                    fill=self._text_color(),
                    font=("Microsoft YaHei", font_size),
                    width=rw - 8,
                )

    def _rect_color(self, entry: FileEntry, index: int) -> str:
        """根据条目类型和大小返回颜色."""
        if not self._entries:
            return "#666666"
        max_size = self._entries[0].size if self._entries else 1
        ratio = entry.size / max(max_size, 1)

        if entry.is_dir:
            # 蓝色系: 深 -> 浅
            r1, g1, b1 = 0x1A, 0x52, 0x76
            r2, g2, b2 = 0x85, 0xC1, 0xE9
        else:
            # 灰色系: 深 -> 浅
            r1, g1, b1 = 0x44, 0x44, 0x44
            r2, g2, b2 = 0xBB, 0xBB, 0xBB

        r = int(r1 + (r2 - r1) * ratio)
        g = int(g1 + (g2 - g1) * ratio)
        b = int(b1 + (b2 - b1) * ratio)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _draw_rect_normal(self, item_id: int):
        """恢复矩形正常外观."""
        entry = self._rect_map.get(item_id)
        if not entry:
            return
        # 找到该 entry 的索引以获取颜色
        try:
            idx = self._entries.index(entry)
        except ValueError:
            idx = 0
        color = self._rect_color(entry, idx)
        self.canvas.itemconfigure(item_id, outline="", width=0, fill=color)

    def _draw_rect_hovered(self, item_id: int):
        """高亮矩形."""
        self.canvas.itemconfigure(item_id, outline="#FFFFFF", width=2)

    def _draw_breadcrumb(self):
        """绘制可点击的面包屑导航."""
        # 清除旧的面包屑标签
        for w in self.breadcrumb_frame.winfo_children():
            w.destroy()

        parts = self._build_breadcrumb(
            self._entries[0].path if self._entries else self._root_path
        )
        if not parts:
            return

        for i, p in enumerate(parts):
            if i > 0:
                sep = ctk.CTkLabel(
                    self.breadcrumb_frame, text=">",
                    font=ctk.CTkFont(size=10), text_color=("#999999", "#777777"),
                )
                sep.pack(side="left")

            if i == 0:
                label_text = f"🏠 {p.rstrip(chr(92))}"
            else:
                label_text = os.path.basename(p)

            lbl = ctk.CTkLabel(
                self.breadcrumb_frame, text=label_text,
                font=ctk.CTkFont(size=11), text_color=("#666666", "#999999"),
                cursor="hand2",
            )
            lbl.pack(side="left")
            # 绑定点击（默认参数捕获当前 i）
            lbl.bind("<Button-1>", lambda e, idx=i: self._on_breadcrumb_click(idx))
            # 悬停效果
            lbl.bind("<Enter>", lambda e, l=lbl: l.configure(
                text_color=("#1A5276", "#64B5F6")))
            lbl.bind("<Leave>", lambda e, l=lbl: l.configure(
                text_color=("#666666", "#999999")))

    def _update_count_status(self):
        """更新底部状态栏的统计信息."""
        file_count = sum(1 for e in self._entries if not e.is_dir)
        dir_count = sum(1 for e in self._entries if e.is_dir)
        total = sum(e.size for e in self._entries)
        self.status_label.configure(
            text=f"📊 共 {len(self._entries)} 个项目（{dir_count} 目录 + {file_count} 文件）  |  💾 总计 {format_bytes(total)}"
        )
