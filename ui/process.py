"""进程管理页面：内存可视化条 + 受保护标记."""

import os
import subprocess
import threading
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

            # 内存列：文字 + 进度条
            mem_frame = ctk.CTkFrame(row, fg_color="transparent", width=100)
            mem_frame.pack(side="left", padx=2)
            ctk.CTkLabel(mem_frame, text=f"{proc['memory_mb']:.0f} MB", width=60, anchor="w",
                         font=ctk.CTkFont(size=11)).pack(side="left")
            mem_bar = ctk.CTkProgressBar(mem_frame, width=35, height=4, corner_radius=2,
                                         progress_color="#27ae60")
            mem_bar.pack(side="left", padx=2)
            mem_bar.set(proc["memory_mb"] / max_mem if max_mem > 0 else 0)

            # 操作列
            if is_protected:
                ctk.CTkLabel(row, text="🔒", width=30, font=ctk.CTkFont(size=11)).pack(side="left")
            else:
                ctk.CTkLabel(row, text="▶", width=30, font=ctk.CTkFont(size=11),
                             text_color="gray60").pack(side="left")

            # 绑定点击
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
        menu.add_separator()
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
        pid = self._selected_pid
        name = self._selected_name
        if not messagebox.askyesno(
            "确认结束进程",
            f"确定要结束 \"{name}\" (PID: {pid}) 吗？\n\n"
            "程序会先尝试正常关闭（保存你的工作），\n"
            "仅当程序无响应时才会强制终止。\n\n"
            "⚠ 注意：强制终止可能导致程序下次无法正常启动。",
            parent=self,
        ):
            return

        # 禁用按钮，显示处理中
        self.kill_btn.configure(state="disabled", text="⏳ 处理中...")
        self.status_label.configure(text=f"正在结束 {name}...")

        # 在后台线程执行杀进程，避免阻塞 UI
        threading.Thread(target=self._do_kill, args=(pid, name), daemon=True).start()

    def _do_kill(self, pid: int, name: str):
        """后台线程：执行杀进程，完成后回调主线程."""
        ok, msg = self.manager.kill_process(pid)
        self.after(0, lambda: self._on_kill_done(pid, name, ok, msg))

    def _on_kill_done(self, pid: int, name: str, ok: bool, msg: str):
        """主线程回调：显示结果并刷新."""
        # 恢复按钮
        self.kill_btn.configure(state="disabled", text="❌ 结束进程")

        if ok:
            if "⚠" in msg:
                messagebox.showwarning("操作完成", msg, parent=self)
            else:
                messagebox.showinfo("成功", msg, parent=self)
        else:
            messagebox.showerror("失败", msg, parent=self)
        self.after(500, self._refresh)

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
