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
            all_entries = self.manager.get_entries()
            # 过滤掉已卸载软件的残留启动项
            self._entries = [e for e in all_entries if not self.manager.is_dead_entry(e)]
            dead_count = len(all_entries) - len(self._entries)
            disabled_list = self.config.get("startup_disabled", [])

            enabled_count = 0
            for i, entry in enumerate(self._entries):
                card = ctk.CTkFrame(self.list_frame, corner_radius=8)
                card.pack(fill="x", pady=2)

                top_row = ctk.CTkFrame(card, fg_color="transparent")
                top_row.pack(fill="x", padx=10, pady=(8, 2))

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

                # 开机耗时估算行
                delay_row = ctk.CTkFrame(card, fg_color="transparent")
                delay_row.pack(fill="x", padx=10, pady=(0, 2))
                delay_text = self.manager.get_boot_delay_estimate(entry)
                ctk.CTkLabel(
                    delay_row, text=delay_text,
                    font=ctk.CTkFont(size=10), text_color="#e67e22",
                ).pack(side="left")

                # 底部行
                bottom_row = ctk.CTkFrame(card, fg_color="transparent")
                bottom_row.pack(fill="x", padx=10, pady=(0, 4))

                cmd = entry.command
                if len(cmd) > 55:
                    cmd = cmd[:52] + "..."
                ctk.CTkLabel(bottom_row, text=cmd, font=ctk.CTkFont(size=10),
                             text_color="gray60").pack(side="left")

                impact = self.manager.get_impact_estimate(entry)
                icon = "❌" if "不存在" in impact else "⚠"
                ctk.CTkLabel(bottom_row, text=f"{icon} {impact}",
                             font=ctk.CTkFont(size=9),
                             text_color="#e74c3c" if "不存在" in impact else "gray60").pack(side="right")

            suffix = f"，已过滤 {dead_count} 个失效项" if dead_count else ""
            self.summary_label.configure(
                text=f"共 {len(self._entries)} 个启动项，{enabled_count} 个已启用{suffix}"
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
