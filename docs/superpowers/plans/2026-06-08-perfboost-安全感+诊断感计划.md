# PerfBoost 安全感+诊断感 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在垃圾清理中增加安全分级（🟢🟡🔴），仪表盘增加一句话诊断，启动项增加开机耗时预估。

**Architecture:** 数据层改动集中在 core/cleaner.py（CleanCategory 新增 risk_level + explanation 字段）和 core/startup.py（新增开机耗时估算方法）。UI 层改动在 ui/cleaner.py（风险标记 + 默认勾选逻辑）、ui/dashboard.py（诊断文本 + 磁盘区分）、ui/startup.py（耗时展示）。

**Tech Stack:** Python 3.11+ / CustomTkinter / psutil / winreg

---

## 总结概括

本次迭代围绕两个用户感知维度展开：**安全感**（让用户知道操作是否安全）和**诊断感**（让用户知道电脑哪里有问题）。

### 改什么

| 页面 | 现在的问题 | 改成什么样 |
|------|-----------|-----------|
| **清理页** | 所有清理项一视同仁，用户不敢勾 | 🟢🟡🔴 三级风险标记 + 大白话解释，安全项默认勾选 |
| **仪表盘** | 只有数字没有判断，用户看不懂 | 顶部一句话诊断：C 盘不足/内存高/一切正常 |
| **启动项** | 只列名字，不知道关了能快多少 | 每项估算开机耗时，给用户"关掉的理由" |

### 三层风险分级

| 等级 | 标签 | 包含 | 默认行为 |
|------|------|------|---------|
| 🟢 安全 | 删了完全不影响使用 | 用户临时文件、浏览器缓存、回收站、崩溃转储 | 默认勾选，全选按钮只切这一层 |
| 🟡 谨慎 | 一般安全但有副作用 | 系统临时文件（需管理员）、缩略图缓存（下次生成略慢） | 默认不勾选 |
| 🔴 高级 | 出问题时排查用，建议保留 | Windows 日志 | 默认不勾选，不参与全选 |

### 一句话诊断规则

- C 盘剩余 < 10G → 🔴 提示清理
- 其他盘剩余 < 10G → 🟡 建议整理
- 内存 > 85% → 🔴 建议结束应用
- CPU > 80% → 🟡 提示查看进程
- 全正常 → 🟢 你的电脑运行良好

### 改动范围

**5 个任务，3 个文件，0 个新文件。**

| 优先级 | 任务 | 文件 | 工作量 |
|--------|------|------|--------|
| P0 | CleanCategory 数据模型扩展 | `core/cleaner.py` | 小 |
| P0 | 清理页风险标记 + 默认勾选 | `ui/cleaner.py` | 中 |
| P1 | 仪表盘一句话诊断 | `ui/dashboard.py` | 中 |
| P1 | 启动项开机耗时估算（Core） | `core/startup.py` | 中 |
| P1 | 启动项页面耗时展示 | `ui/startup.py` | 小 |

所有改动向后兼容，不破坏现有功能。

---

## 文件变更地图

| 文件 | 动作 | 内容 |
|------|------|------|
| `core/cleaner.py:38-46` | 修改 | CleanCategory 增加 risk_level、explanation 字段 |
| `core/cleaner.py:59-129` | 修改 | scan() 中为每个类别赋值风险等级和解释 |
| `core/startup.py:155-221` | 修改 | 新增 get_boot_delay_estimate() 方法 |
| `ui/cleaner.py:78-122` | 修改 | 渲染风险标记 + 解释文案 + 默认勾选逻辑 |
| `ui/cleaner.py:22-55` | 修改 | 页面顶部增加清理范围提示 + 全选只切换绿色 |
| `ui/dashboard.py:14-41` | 修改 | 卡片上方增加诊断文本 + 区分 C 盘和其他盘 |
| `ui/startup.py:60-103` | 修改 | 卡片中增加开机耗时显示行 |

无新增文件。

---

### Task 1: CleanCategory 数据模型扩展

**Files:**
- Modify: `core/cleaner.py:38-46`
- Modify: `core/cleaner.py:59-129`

- [ ] **Step 1: 给 CleanCategory 增加 risk_level 和 explanation 字段**

将 `core/cleaner.py` 中 CleanCategory 的 dataclass 定义修改为：

```python
@dataclass
class CleanCategory:
    key: str
    label: str
    paths: list[str] = field(default_factory=list)
    total_size: int = 0
    files: list[tuple[str, int]] = field(default_factory=list)
    needs_admin: bool = False
    risk_level: str = "safe"          # "safe" | "caution" | "danger"
    explanation: str = ""             # 大白话解释
```

- [ ] **Step 2: 在 scan() 方法中为每个类别赋值**

将 `core/cleaner.py` 的 `scan()` 方法中每个 CleanCategory 构造处修改为：

```python
def scan(self) -> list[CleanCategory]:
    self._categories = []

    # 1. 用户临时文件
    user_temp = os.environ.get("TEMP") or os.environ.get("TMP") or ""
    temp_cat = CleanCategory(
        key="temp", label="用户临时文件", needs_admin=False,
        risk_level="safe",
        explanation="软件运行时产生的临时文件，删了完全不影响使用",
    )
    if user_temp and os.path.isdir(user_temp):
        temp_cat.paths.append(user_temp)
    self._collect_files(temp_cat)
    self._categories.append(temp_cat)

    # 2. 浏览器缓存
    browser_paths = _get_browser_cache_paths()
    browser_cat = CleanCategory(
        key="browser_cache", label="浏览器缓存", needs_admin=False,
        paths=browser_paths,
        risk_level="safe",
        explanation="浏览器存的网页图片和文件，删了不影响密码和收藏，网页重新加载即可",
    )
    self._collect_files(browser_cat)
    self._categories.append(browser_cat)

    # 3. 回收站
    recycle_cat = CleanCategory(
        key="recycle_bin", label="回收站", needs_admin=False,
        risk_level="safe",
        explanation="你已经删过的文件，清空后释放它们占用的空间",
    )
    recycle_cat.total_size = _get_recycle_bin_size_shell()
    self._categories.append(recycle_cat)

    # 4. 错误报告
    crash_dirs = _get_crash_dump_dirs()
    crash_cat = CleanCategory(
        key="crash_dumps", label="错误报告 & 崩溃转储", needs_admin=False,
        paths=crash_dirs,
        risk_level="safe",
        explanation="软件崩溃时生成的调试文件，对普通用户没任何用处",
    )
    self._collect_files(crash_cat)
    self._categories.append(crash_cat)

    # 5. 系统临时文件
    system_root = os.environ.get("SystemRoot", r"C:\Windows")
    sys_temp = os.path.join(system_root, "Temp")
    sys_temp_cat = CleanCategory(
        key="system_temp", label="系统临时文件",
        paths=[sys_temp] if os.path.isdir(sys_temp) else [],
        needs_admin=True,
        risk_level="caution",
        explanation="Windows 自己的临时文件，一般安全但需要管理员权限",
    )
    self._collect_files(sys_temp_cat)
    self._categories.append(sys_temp_cat)

    # 6. Windows 日志
    log_dirs = [
        os.path.join(system_root, "Logs"),
        os.path.join(system_root, "System32", "winevt", "Logs"),
    ]
    log_cat = CleanCategory(
        key="windows_logs", label="Windows 日志文件",
        paths=[d for d in log_dirs if os.path.isdir(d)],
        needs_admin=True,
        risk_level="danger",
        explanation="系统运行记录，出问题时排查用，建议保留",
    )
    self._collect_files(log_cat)
    self._categories.append(log_cat)

    # 7. 缩略图缓存
    thumb_cat = CleanCategory(
        key="thumbnails", label="缩略图缓存", needs_admin=True,
        risk_level="caution",
        explanation="文件夹里图片视频的预览小图，删了下次打开文件夹会重新生成，略慢",
    )
    thumb_paths = _find_thumbcache_files(system_root)
    thumb_cat.paths = thumb_paths
    thumb_cat.total_size = sum(
        os.path.getsize(p) for p in thumb_paths if os.path.isfile(p)
    )
    for p in thumb_paths:
        if os.path.isfile(p):
            thumb_cat.files.append((p, os.path.getsize(p)))
    self._categories.append(thumb_cat)

    return self._categories
```

- [ ] **Step 3: 验证 run**

```bash
python main.py
```

点击清理 → 扫描，确认程序不报错。

- [ ] **Step 4: Commit**

```bash
git add core/cleaner.py
git commit -m "feat: CleanCategory 增加 risk_level 和 explanation 字段"
```

---

### Task 2: 清理页面 — 风险标记 + 默认勾选 + 范围提示

**Files:**
- Modify: `ui/cleaner.py:22-55` (工具栏：增加范围提示 + 全选只切绿色)
- Modify: `ui/cleaner.py:78-122` (_render_categories：渲染风险标记和解释)

- [ ] **Step 1: 页面顶部增加清理范围提示**

在 `_build_ui()` 方法中，标题下方增加一行提示文字。修改 `ui/cleaner.py` `_build_ui` 方法中标题行之后的代码：

```python
def _build_ui(self):
    ctk.CTkLabel(
        self, text="垃圾清理",
        font=ctk.CTkFont(size=20, weight="bold"),
    ).pack(anchor="w", padx=20, pady=(15, 10))

    # 新增：清理范围提示
    ctk.CTkLabel(
        self, text="💡 清理范围：系统临时文件、浏览器缓存等，主要释放 C 盘空间",
        font=ctk.CTkFont(size=11), text_color="gray60",
    ).pack(anchor="w", padx=20, pady=(0, 8))

    # 工具栏 ...（保持原有代码）
```

- [ ] **Step 2: 修改全选逻辑 — 只切换安全类别**

修改 `_toggle_all` 方法，遍历 checkbox 时只切换 risk_level 为 "safe" 的类别：

```python
def _toggle_all(self):
    state = self._all_var.get()
    for cat in self._categories:
        if cat.risk_level == "safe":
            if cat.key in self._checkboxes:
                self._checkboxes[cat.key].set(state)
```

- [ ] **Step 3: 修改 _render_categories — 渲染风险标记和解释**

修改 `_render_categories` 方法，在每个类别卡片中增加风险标记和解释文案。替换现有的卡片渲染部分：

```python
def _render_categories(self):
    for w in self.cat_container.winfo_children():
        w.destroy()
    self._checkboxes.clear()

    saved = self.config.get("clean_categories", {})
    max_size = max((c.total_size for c in self._categories), default=1)

    # 风险级别对应的颜色和标签
    RISK_CONFIG = {
        "safe":    {"badge": "🟢 安全", "color": "#27ae60", "fg": ("#E8F5E9", "#1B3A1B")},
        "caution": {"badge": "🟡 谨慎", "color": "#f39c12", "fg": ("#FFF8E1", "#3A3010")},
        "danger":  {"badge": "🔴 高级", "color": "#e74c3c", "fg": ("#FDEDEC", "#3A1515")},
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
```

- [ ] **Step 4: run 验证**

```bash
python main.py
```

进入清理页 → 点击扫描，确认：
- 每行显示 🟢/🟡/🔴 风险标记
- 绿色类别默认勾选，黄色/红色默认不勾
- 全选按钮只切换绿色类别
- 顶部显示 C 盘范围提示
- 每行显示大白话解释

- [ ] **Step 5: Commit**

```bash
git add ui/cleaner.py
git commit -m "feat: 清理页增加风险标记、默认安全勾选、范围提示"
```

---

### Task 3: 仪表盘 — 一句话诊断 + 磁盘区分

**Files:**
- Modify: `ui/dashboard.py:14-41` (_build_ui: 增加诊断标签)
- Modify: `ui/dashboard.py:107-135` (update_display: 构建诊断文本)
- Modify: `ui/dashboard.py:136-158` (_update_disks: 区分 C 盘和其他盘)

- [ ] **Step 1: 在 _build_ui 中增加诊断标签**

修改 `ui/dashboard.py` 的 `_build_ui` 方法，在标题和第一行卡片之间插入诊断标签：

```python
def _build_ui(self):
    ctk.CTkLabel(
        self, text="系统仪表盘",
        font=ctk.CTkFont(size=20, weight="bold"),
    ).pack(anchor="w", padx=20, pady=(15, 10))

    # 新增：一句话诊断
    self.diagnosis_label = ctk.CTkLabel(
        self, text="",
        font=ctk.CTkFont(size=12),
        text_color=("#333333", "#CCCCCC"),
    )
    self.diagnosis_label.pack(anchor="w", padx=20, pady=(0, 12))

    # 第一行：CPU + 内存（保持不变）
    row1 = ctk.CTkFrame(self, fg_color="transparent")
    row1.pack(fill="x", padx=15, pady=(0, 10))
    ...
```

- [ ] **Step 2: 在 update_display 中计算并设置诊断文本**

修改 `ui/dashboard.py` 的 `update_display` 方法，增加诊断逻辑：

```python
def update_display(self, data: dict):
    cpu = data["cpu_percent"]
    self.cpu_label.configure(text=f"{cpu:.0f}%")
    self.cpu_bar.set(cpu / 100)

    # ... (CPU temp, memory, boot time 保持原有代码) ...

    self._update_disks(data.get("disks", []))
    self._update_network(data.get("net_upload", 0), data.get("net_download", 0))

    # 新增：诊断逻辑（放在最后，可引用磁盘数据）
    self._update_diagnosis(data)
```

- [ ] **Step 3: 实现 _update_diagnosis 方法**

在 `ui/dashboard.py` 的 `DashboardFrame` 类中新增方法：

```python
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

    # 多条用换行拼接
    self.diagnosis_label.configure(text="\n".join(messages))
```

- [ ] **Step 4: 修改磁盘卡片 — C 盘和 D/E 盘视觉区分**

修改 `_update_disks` 方法，为 C 盘和其他盘使用不同颜色标记：

```python
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
```

- [ ] **Step 5: run 验证**

```bash
python main.py
```

确认仪表盘：
- 上方显示诊断文字（正常时显示"🟢 你的电脑运行良好"）
- 如果有磁盘空间不足、内存高、CPU 高，显示对应红色/黄色文字
- C 盘和其他盘进度条颜色不同

- [ ] **Step 6: Commit**

```bash
git add ui/dashboard.py
git commit -m "feat: 仪表盘增加一句话诊断和磁盘区分"
```

---

### Task 4: 启动项 — 开机耗时估算（Core 层）

**Files:**
- Modify: `core/startup.py:155-221` (新增 get_boot_delay_estimate 方法)

- [ ] **Step 1: 新增 get_boot_delay_estimate 静态方法**

在 `core/startup.py` 的 `StartupManager` 类中，`get_impact_estimate` 方法之后新增：

```python
@staticmethod
def get_boot_delay_estimate(entry) -> str:
    """估算启动项对开机时间的拖慢程度，返回一句人话。

    根据程序 exe 文件大小粗略估算。不追求精确计时，
    目的是给用户一个"关掉的理由"。
    """
    # 启动文件夹快捷方式 — 解析 .lnk 指向的真实目标
    if entry.command.lower().endswith(".lnk"):
        target = StartupManager._resolve_lnk_target(entry.command)
        if not target or not os.path.exists(target):
            return "该程序已卸载，可安全禁用"
        exe_path = target
    else:
        exe_path = StartupManager._extract_exe_path(entry.command)

    if not exe_path or not os.path.exists(exe_path):
        return "该程序已卸载，可安全禁用"

    # 获取 exe 大小（MB）
    try:
        size_mb = os.path.getsize(exe_path) / (1024 * 1024)
    except OSError:
        return "无法评估｜可手动禁用"

    # 粗略估算：每 10MB 约 0.3 秒，最低 0.3 秒，最高 15 秒
    delay = max(0.3, min(15.0, size_mb * 0.03))
    return f"⏱ 预估拖慢开机 {delay:.1f} 秒"
```

- [ ] **Step 2: run 验证**

```bash
python main.py
```

确认不报错。

- [ ] **Step 3: Commit**

```bash
git add core/startup.py
git commit -m "feat: 启动项增加开机耗时估算方法"
```

---

### Task 5: 启动项页面 — 显示开机耗时

**Files:**
- Modify: `ui/startup.py:60-103` (_refresh 方法：卡片中增加耗时行)

- [ ] **Step 1: 在启动项卡片中增加耗时显示**

修改 `ui/startup.py` `_refresh` 方法中的卡片渲染，在底部行（bottom_row）之前增加耗时显示行：

找到 `_refresh` 方法中构建每个卡片的代码（约在第 56-103 行），在 bottom_row 之上插入一个耗时行：

```python
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

            # 新增：开机耗时估算行
            delay_row = ctk.CTkFrame(card, fg_color="transparent")
            delay_row.pack(fill="x", padx=10, pady=(0, 2))
            delay_text = self.manager.get_boot_delay_estimate(entry)
            ctk.CTkLabel(
                delay_row, text=delay_text,
                font=ctk.CTkFont(size=10), text_color="#e67e22",
            ).pack(side="left")

            # 底部行（原有代码：命令路径 + 影响评估）
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

        self.summary_label.configure(
            text=f"共 {len(self._entries)} 个启动项，{enabled_count} 个已启用"
        )
    except Exception as e:
        ctk.CTkLabel(self.list_frame, text=f"加载失败: {e}").pack()
```

- [ ] **Step 2: run 验证**

```bash
python main.py
```

进入启动项页面，确认：
- 每个启动项卡片显示 "⏱ 预估拖慢开机 X.X 秒"（橙色）
- 已卸载的程序显示 "该程序已卸载，可安全禁用"

- [ ] **Step 3: Commit**

```bash
git add ui/startup.py
git commit -m "feat: 启动项页面显示开机耗时预估"
```

---

## 验证清单

实施完成后逐项检查：

- [ ] 清理页扫描后，每行显示 🟢🟡🔴 风险标记
- [ ] 🟢 类别默认勾选，🟡🔴 默认不勾
- [ ] 全选只切 🟢，不碰 🟡🔴
- [ ] 每行有大白话解释文字
- [ ] 清理页顶部有 C 盘范围提示
- [ ] 仪表盘有诊断文字（正常：🟢 良好 / 异常：🔴 提示）
- [ ] C 盘和其他盘空间不足时诊断文本不同
- [ ] 启动项每行有开机耗时预估
- [ ] 已卸载的启动项提示"可安全禁用"
