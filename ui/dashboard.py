"""仪表盘页面：4 张数据卡片 — CPU/内存/磁盘/网络."""

import customtkinter as ctk

from utils.helpers import format_bytes


class DashboardFrame(ctk.CTkFrame):
    def __init__(self, master, config, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.config = config
        self._build_ui()

    def _build_ui(self):
        ctk.CTkLabel(
            self, text="系统仪表盘",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(anchor="w", padx=20, pady=(15, 10))

        # 一句话诊断
        self.diagnosis_label = ctk.CTkLabel(
            self, text="",
            font=ctk.CTkFont(size=12),
            text_color=("#333333", "#CCCCCC"),
        )
        self.diagnosis_label.pack(anchor="w", padx=20, pady=(0, 12))

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

        # 底部状态行：开机时间
        status_row = ctk.CTkFrame(self, fg_color=("#E8E8E8", "#1A1A1A"), corner_radius=8)
        status_row.pack(fill="x", padx=15, pady=(0, 10))
        self.boot_label = ctk.CTkLabel(
            status_row, text="💻 开机时间: --",
            font=ctk.CTkFont(size=12), text_color=("#555555", "#888888"),
        )
        self.boot_label.pack(padx=14, pady=8)

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
        cpu = data["cpu_percent"]
        self.cpu_label.configure(text=f"{cpu:.0f}%")
        self.cpu_bar.set(cpu / 100)

        mem_pct = data["memory_percent"]
        self.mem_pct_label.configure(text=f"{mem_pct:.0f}%")
        self.mem_bar.set(mem_pct / 100)
        self.mem_detail_label.configure(
            text=f"{format_bytes(data['memory_used'])} / {format_bytes(data['memory_total'])}"
        )

        # 开机时间
        bh = data.get("_boot_hours")
        bm = data.get("_boot_minutes")
        if bh is not None:
            self.boot_label.configure(text=f"💻 已开机 {bh} 小时 {bm} 分钟")
        else:
            self.boot_label.configure(text="💻 开机时间: --")

        self._update_disks(data.get("disks", []))
        self._update_network(data.get("net_upload", 0), data.get("net_download", 0))
        self._update_diagnosis(data)

    def _update_disks(self, disks: list[dict]):
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

        for i, widget in enumerate(self._disk_widgets):
            if i < len(disks):
                d = disks[i]
                widget["label"].configure(text=f"{d['mountpoint']} ")
                widget["bar"].set(d["percent"] / 100)
                widget["detail"].configure(
                    text=f"{format_bytes(d['used'])}/{format_bytes(d['total'])}"
                )
                # C 盘用蓝色进度条，其他盘用绿色
                if d["mountpoint"] == "C:\\":
                    widget["bar"].configure(progress_color="#3498db")
                else:
                    widget["bar"].configure(progress_color="#27ae60")

    def _update_diagnosis(self, data: dict):
        """根据当前系统数据生成一句话诊断."""
        messages = []
        disks = data.get("disks", [])
        mem_pct = data.get("memory_percent", 0)
        cpu_pct = data.get("cpu_percent", 0)

        # C 盘检查
        for d in disks:
            free_gb = (d["total"] - d["used"]) / (1024**3)
            if d["mountpoint"] == "C:\\" and free_gb < 10:
                messages.append(
                    f'🔴 C 盘剩余 {free_gb:.1f} GB，建议清理垃圾释放空间'
                )
            elif d["mountpoint"] != "C:\\" and free_gb < 10:
                label = d["mountpoint"].rstrip(":\\")
                messages.append(
                    f'🟡 {label} 盘剩余 {free_gb:.1f} GB，建议手动整理文件'
                )

        # 内存检查
        if mem_pct > 85:
            messages.append("🔴 内存占用较高，可以结束一些后台应用")

        # CPU 检查
        if cpu_pct > 80:
            messages.append("🟡 CPU 负载较高，可在进程页查看原因")

        # 默认
        if not messages:
            messages.append("🟢 你的电脑运行良好")

        self.diagnosis_label.configure(text="\n".join(messages))

    def _update_network(self, upload, download):
        self.net_upload_label.configure(text=f"↑ {format_bytes(int(upload))}/s")
        self.net_download_label.configure(text=f"↓ {format_bytes(int(download))}/s")
