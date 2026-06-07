"""清理页面：卡片式分类列表."""

import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime

from core.cleaner import JunkCleaner
from utils.helpers import format_bytes, is_admin, relaunch_as_admin
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
        ctk.CTkLabel(
            self, text="垃圾清理",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(anchor="w", padx=20, pady=(15, 10))

        # 清理范围提示
        ctk.CTkLabel(
            self, text="💡 清理范围：系统临时文件、浏览器缓存等，主要释放 C 盘空间",
            font=ctk.CTkFont(size=11), text_color="gray60",
        ).pack(anchor="w", padx=20, pady=(0, 8))

        # 工具栏
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", padx=20, pady=(0, 10))

        self.scan_btn = ctk.CTkButton(toolbar, text="🔍 扫描垃圾文件", command=self._on_scan)
        self.scan_btn.pack(side="left", padx=(0, 5))

        self.clean_btn = ctk.CTkButton(
            toolbar, text="🧹 一键清理", command=self._on_clean,
            state="disabled", fg_color="#c0392b", hover_color="#e74c3c",
        )
        self.clean_btn.pack(side="left", padx=5)

        ctk.CTkCheckBox(
            toolbar, text="全选", variable=self._all_var,
            command=self._toggle_all,
        ).pack(side="right", padx=5)

        # 状态
        self.status_label = ctk.CTkLabel(
            self, text="就绪 — 点击扫描开始",
            font=ctk.CTkFont(size=11), text_color="gray60",
        )
        self.status_label.pack(anchor="w", padx=20, pady=(0, 5))

        # 分类卡片
        self.cat_container = ctk.CTkScrollableFrame(self)
        self.cat_container.pack(fill="both", expand=True, padx=15, pady=(0, 10))

    def _toggle_all(self):
        state = self._all_var.get()
        for cat in self._categories:
            if cat.risk_level == "safe":
                if cat.key in self._checkboxes:
                    self._checkboxes[cat.key].set(state)

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

        # 风险级别对应的颜色和标签
        RISK_CONFIG = {
            "safe":    {"badge": "🟢 安全", "color": "#27ae60"},
            "caution": {"badge": "🟡 谨慎", "color": "#f39c12"},
            "danger":  {"badge": "🔴 高级", "color": "#e74c3c"},
        }

        for cat in self._categories:
            risk = RISK_CONFIG.get(cat.risk_level, RISK_CONFIG["safe"])
            card = ctk.CTkFrame(self.cat_container, corner_radius=8)
            card.pack(fill="x", pady=3)

            # 第一行：风险标记 + 名称 + 大小 + 复选框
            row1 = ctk.CTkFrame(card, fg_color="transparent")
            row1.pack(fill="x", padx=10, pady=(8, 2))

            # 风险徽章
            badge = ctk.CTkLabel(
                row1, text=risk["badge"],
                font=ctk.CTkFont(size=10), text_color=risk["color"],
            )
            badge.pack(side="left", padx=(0, 6))

            # 复选框：安全类别默认勾选，非安全类别默认不勾选
            if cat.risk_level == "safe":
                default_checked = saved.get(cat.key, True)
            else:
                default_checked = saved.get(cat.key, False)

            var = ctk.BooleanVar(value=default_checked)
            cb = ctk.CTkCheckBox(row1, text=cat.label, variable=var)
            cb.pack(side="left")
            self._checkboxes[cat.key] = var

            ctk.CTkLabel(row1, text=format_bytes(cat.total_size), width=80,
                         font=ctk.CTkFont(size=12, weight="bold")).pack(side="right")

            if cat.needs_admin:
                ctk.CTkLabel(row1, text="🔒", font=ctk.CTkFont(size=10)).pack(side="right", padx=(0, 4))

            # 第二行：大白话解释
            row_explain = ctk.CTkFrame(card, fg_color="transparent")
            row_explain.pack(fill="x", padx=10, pady=(0, 2))
            ctk.CTkLabel(
                row_explain, text=cat.explanation,
                font=ctk.CTkFont(size=10), text_color="gray60",
            ).pack(anchor="w")

            # 第三行：进度条 + 文件数 + 预览
            row2 = ctk.CTkFrame(card, fg_color="transparent")
            row2.pack(fill="x", padx=10, pady=(0, 8))

            bar = ctk.CTkProgressBar(row2, height=6, corner_radius=3)
            bar.pack(side="left", fill="x", expand=True)
            bar.set(cat.total_size / max_size if max_size > 0 else 0)

            if cat.files and cat.key != "recycle_bin":
                ctk.CTkLabel(row2, text=f"{len(cat.files)} 个文件",
                             font=ctk.CTkFont(size=10), text_color="gray60").pack(side="left", padx=(8, 0))
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

        # ---- 管理员权限检查 ----
        needs_admin_keys = {
            c.key for c in self._categories
            if c.key in selected and c.needs_admin
        }
        if needs_admin_keys and not is_admin():
            admin_labels = [
                c.label for c in self._categories
                if c.key in needs_admin_keys
            ]
            choice = messagebox.askyesnocancel(
                "需要管理员权限",
                "以下类别需要管理员权限才能清理：\n\n"
                + "\n".join(f"• {l}" for l in admin_labels)
                + "\n\n是否以管理员身份重新运行 PerfBoost？\n\n"
                + "【是】以管理员身份重启（需重新扫描）\n"
                + "【否】跳过这些项目，仅清理不需要权限的\n"
                + "【取消】不做任何操作",
                parent=self,
            )
            if choice is None:  # 取消
                return
            if choice:  # 是 — 重启为管理员
                relaunch_as_admin()
                return  # 不会执行到这里，但保留以防万一
            # 否 — 跳过管理员项
            selected = selected - needs_admin_keys
            if not selected:
                self.status_label.configure(
                    text="已跳过管理员权限项，无需清理的普通项"
                )
                return

        # ---- 确认弹窗 ----
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
            freed, deleted, failed, pending = self.cleaner.clean(selected)

            total_cleaned = self.config.get("total_cleaned_bytes", 0) + freed
            self.config.set("total_cleaned_bytes", total_cleaned)
            self.config.set("last_optimization", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

            result_msg = f"✅ 已释放: {format_bytes(freed)}"
            if pending:
                result_msg += f"\n\n🔄 {len(pending)} 项文件被占用，已标记重启后自动删除"
            if failed:
                result_msg += "\n\n⚠ 以下文件无法删除：\n"
                for f in failed[:5]:
                    result_msg += f"• {f}\n"
                if len(failed) > 5:
                    result_msg += f"…共 {len(failed)} 项\n"
            messagebox.showinfo("清理结果", result_msg, parent=self)
            self.status_label.configure(text=f"✅ 清理完成！释放 {format_bytes(freed)}")
        except Exception as e:
            messagebox.showerror("清理出错", str(e), parent=self)
            self.status_label.configure(text=f"清理出错: {e}")
        finally:
            self.clean_btn.configure(state="normal", text="🧹 一键清理")
            self._on_scan()
