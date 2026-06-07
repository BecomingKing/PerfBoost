# PerfBoost V1 改良计划

> 日期: 2026-06-07 | 状态: 待审批

## 📋 计划概览

**目标：** 在 PerfBoost v1 基础上实施 10 项产品化改进，将其从开发者自用工具升级为可公开分发的桌面产品。

**技术栈：** Python 3.11+ / CustomTkinter (GUI) / psutil (系统信息) / winreg (注册表) / pystray (托盘) / Pillow (图标) / pytest (测试)

**架构：** 保持三层分离 `ui/ → core/ → utils/`，新增 `core/tray.py`（系统托盘）、`ui/welcome.py`（引导向导）、`ui/settings.py`（设置 Tab）、`tests/`（单元测试）。

**数据流：** 系统还原点(PowerShell) + 备份恢复(JSON) + 托盘事件(回调)
### Task 依赖关系

```
Phase A: 基础设施 (无依赖)
  ├─→ A1: requirements.txt + 安装依赖
  ├─→ A2: config.py (新增键)
  └─→ A3: helpers.py (boot_time)

Phase B: Core 层 (依赖 Phase A)
  ├─→ B1: core/cleaner.py    (预览+还原点)
  ├─→ B2: core/startup.py    (备份+恢复)
  ├─→ B3: core/tray.py       (NEW)

Phase C: UI 层 (依赖 Phase B)
  ├─→ C1: ui/dashboard.py    (优化统计升级)
  ├─→ C2: ui/cleaner.py      (预览+确认)
  ├─→ C3: ui/startup.py      (恢复+影响评估)
  ├─→ C4: ui/process.py      (点击选中+右键)
  ├─→ C5: ui/welcome.py      (NEW)
  └─→ C6: ui/settings.py     (NEW)

Phase D: App 集成 (依赖 Phase C)
  └─→ D1: app.py             (托盘+设置Tab+主题+welcome)

Phase E: 测试 + 文档 (依赖 Phase D)
  ├─→ E1: tests/             (5个测试文件)
  └─→ E2: README.md + BUILD.md
```

### Task 清单

| # | Task | 产出文件 | 作用 |
|---|------|---------|------|
| A1 | 依赖更新 | `requirements.txt` | 新增 pystray（托盘）、Pillow（图标）、pytest（测试）三个依赖包 |
| A2 | Config 扩展 | `utils/config.py` | 新增 `first_run` 键控制首次引导是否显示，`theme` 键持久化用户主题偏好 |
| A3 | Helpers 扩展 | `utils/helpers.py` | 新增 `get_boot_time()` 获取系统开机时间用于仪表盘展示，`get_theme_from_registry()` 首次启动自动匹配 Windows 主题 |
| B1 | 清理安全网 | `core/cleaner.py` | 扫描时收集可预览的文件列表，删除前创建系统还原点（可回滚） |
| B2 | 启动项恢复 | `core/startup.py` | 禁用前先备份条目到 JSON 文件，提供恢复接口|
| B3 | 系统托盘 | `core/tray.py` | 关闭窗口最小化到托盘而非退出，后台监控 CPU/内存超阈值时气球通知，右键菜单控制显隐和退出 |
| C1 | 仪表盘升级 | `ui/dashboard.py` | 升级统计卡片展示累计释放空间和上次优化时间，新增开机时长展示 |
| C2 | 清理 Tab 升级 | `ui/cleaner.py` | 每个类别新增预览按钮查看具体文件，清理前弹出确认弹窗防止误操作 |
| C3 | 启动项 Tab 升级 | `ui/startup.py` | 新增已禁用备份列表弹窗支持一键恢复，每行显示影响评估提示 |
| C4 | 进程 Tab 升级 | `ui/process.py` | 点击行选中进程（高亮），直接点结束进程按钮+确认弹窗替代输 PID，右键菜单支持打开文件位置 |
| C5 | 引导向导 | `ui/welcome.py` | 首次启动弹出 4 页卡片式引导介绍每个功能模块，勾选"不再显示"后永久跳过 |
| C6 | 设置 Tab | `ui/settings.py` | 提供外观模式（暗色/亮色/跟随系统）、监控采样间隔、温度单位三个可调项 |
| D1 | App 集成 | `app.py` | 串联所有新增模块：添加第 5 个设置 Tab、启动欢迎引导判断、注册托盘、应用主题 |
| E1 | 单元测试 | `tests/` (5 files) | 覆盖 helpers / config / monitor / cleaner 核心逻辑，保证后续改动不破坏现有功能 |
| E2 | 分发文档 | `README.md`, `BUILD.md` | 补充打包 exe、数字签名、杀软误报处理说明，降低用户使用门槛 |

**总文件数：** 5 个新文件 + 11 个修改文件 = 16 个文件
**预估工作量：** 每个 Task 10-20 分钟，总计约 3-4 小时

---

## 改动清单

### P0-1: 清理安全网

**改 `core/cleaner.py`:**
- `CleanCategory` dataclass 新增 `files: list[tuple[str, int]]` 字段（文件路径+大小）
- `scan()` 方法在扫描时收集每个文件到 `files` 列表（限制前 500 个文件避免内存爆炸）
- `clean()` 方法新增 `dry_run=False` 参数，dry_run 模式下只返回文件列表不删除
- `clean()` 方法执行前调用 PowerShell 创建系统还原点

**改 `utils/config.py`:**
**改 `ui/cleaner.py`:**
- 每行分类右侧新增"预览"按钮，弹出对话框展示部分文件列表
- 清理按钮改为两步确认："分析 → 确认清理弹窗显示影响 → 执行"

### P0-2: 启动项恢复机制

**改 `core/startup.py`:**
- 新增 `BACKUP_DIR` 常量: `%APPDATA%/PerfBoost/backup/`
- `disable_entry()` 执行前先将完整信息写入 `startup_backup.json`
- 新增 `get_backups() → list[StartupEntry]` 方法
- 新增 `restore_entry(entry) → bool` 方法
- 新增 `get_impact_estimate(entry) → dict` 方法（通过检查文件是否存在判断影响）

**改 `ui/startup.py`:**
- 新增"备份列表"按钮 + 弹窗展示已禁用的条目，支持恢复
- 每行显示影响评估（如"文件不存在｜可能已卸载"）

### P0-3: 进程一键终止

**改 `ui/process.py`:**
- 列表每行改为可点击选中（高亮该行背景色）
- 新增 `_selected_pid` 状态
- 删除 PID 输入弹窗，改为直接"结束进程"按钮（选中后可用）
- 新增确认弹窗："确定要终止 [进程名] (PID: xxx) 吗？"
- 新增右键菜单：结束进程、打开文件位置

### P1-4: 首次使用引导

**新增 `ui/welcome.py`:**
- `WelcomeDialog(ctk.CTkToplevel)` — 模态引导窗口
- 4 页卡片式引导（仪表盘→清理→启动项→进程），每页有图标+说明
- "不再显示"勾选框 + "开始使用"按钮
- 按 `config.get("first_run", True)` 控制是否显示

### P1-5: 仪表盘优化统计升级

**改 `ui/dashboard.py`:**
- 新增"优化统计"卡片替换现有简单摘要
- 显示累计释放空间和上次优化时间（复用现有 config 的 total_cleaned_bytes + last_optimization）
- 最近优化时间（从 config 读取 last_optimization）
- 开机时间显示（通过 psutil.boot_time() 计算）

### P1-6: 系统托盘常驻

**新增 `core/tray.py`:**
- `SystemTray` 类封装 `pystray` + `PIL.Image`
- 功能: 左键双击显示窗口、右键菜单（显示/隐藏/退出）
- 资源异常告警: CPU > 90% 或内存 > 90% 时弹出气球通知
- 默认关闭行为: 最小化到托盘而非退出

**改 `app.py`:**
- 检测 `pystray` 是否可用（try/except ImportError），不可用时回退到直接退出
- `_on_close()` 改为 `self.root.withdraw()` + 托盘通知

### P2-7: 亮暗主题切换

**新增 `ui/settings.py`:**
- 外观模式: 暗色/亮色/跟随系统
- 监控间隔: 1s/2s/5s 下拉选择
- 温度单位: 摄氏度/华氏度

**集成到 app.py:**
- TabView 新增第 5 个 Tab: "⚙️ 设置"
- `ctk.set_appearance_mode()` 读取 config 调用
- 首次启动自动检测 Windows 注册表 `AppsUseLightTheme` 键

### P2-8: 分发文档

- 更新 `README.md` 加入: 打包命令、数字签名说明、杀软误报处理
- 新增 `BUILD.md` 专门讲打包分发

### P2-9: 单元测试

**新增 `tests/`:**
- `tests/test_helpers.py` — format_bytes, is_admin, is_safe_path, get_directory_size
- `tests/test_config.py` — 单例、默认值、读写
- `tests/test_monitor.py` — 采样结构验证
- `tests/test_cleaner.py` — 扫描结构、dry_run

**改 `requirements.txt`:**
- 新增 `pytest>=7.0.0`

---

## 依赖变更

```
customtkinter>=5.2.0    # 现有
psutil>=5.9.0           # 现有
pystray>=0.19.0         # 系统托盘 (NEW)
Pillow>=10.0.0          # 托盘图标 + pystray 依赖 (NEW)
pytest>=7.0.0           # 测试 (NEW)
```

---

## 文件清单

| 操作 | 文件 | 说明 |
|------|------|------|
| **NEW** | `core/tray.py` | 系统托盘封装 |
| **NEW** | `ui/welcome.py` | 首次引导向导 |
| **NEW** | `ui/settings.py` | 设置 Tab |
| **NEW** | `tests/` (5 files) | pytest 测试 |
| **MOD** | `core/cleaner.py` | 预览+还原点 |
| **MOD** | `core/startup.py` | 备份+恢复 |
| **MOD** | `core/monitor.py` | 新增 boot_time |
| **MOD** | `ui/cleaner.py` | 预览+确认 |
| **MOD** | `ui/startup.py` | 恢复按钮+影响评估 |
| **MOD** | `ui/process.py` | 点击选中+右键菜单 |
| **MOD** | `ui/dashboard.py` | 优化统计+开机时间 |
| **MOD** | `app.py` | 托盘+设置+主题 |
| **MOD** | `utils/config.py` | 新增配置键 |
| **MOD** | `utils/helpers.py` | 新增开机时间函数 |
| **MOD** | `requirements.txt` | 新增依赖 |

---

## 执行顺序

```
Phase A: 基础设施
  → Task A1: 更新 requirements.txt + 安装依赖
  → Task A2: 扩展 utils/config.py (新增键)
  → Task A3: 扩展 utils/helpers.py (boot_time)

Phase B: Core 层改进
  → Task B1: core/cleaner.py (预览+还原点)
  → Task B2: core/startup.py (备份+恢复)
  → Task B3: core/tray.py (NEW)

Phase C: UI 层改进
  → Task C1: ui/dashboard.py (优化统计升级)
  → Task C2: ui/cleaner.py (预览+确认)
  → Task C3: ui/startup.py (恢复+影响评估)
  → Task C4: ui/process.py (点击选中+右键)
  → Task C5: ui/welcome.py (NEW)
  → Task C6: ui/settings.py (NEW)

Phase D: App 集成
  → Task D1: app.py 大改 (托盘+设置Tab+主题+welcome)

Phase E: 测试 + 文档
  → Task E1: tests/ (5个测试文件)
  → Task E2: README.md + BUILD.md
```

---

## 验证方式

1. `python -m pytest tests/ -v` — 所有测试通过
2. `python main.py` — 应用启动，5 个 Tab 正常切换
3. 首次运行应弹出 Welcome 向导
4. 设置 Tab 切换暗/亮主题即时生效
5. 关闭窗口后托盘图标出现，右键菜单正常
6. 清理 Tab 扫描后可预览文件列表，需要确认才执行
7. 进程 Tab 点击行高亮，直接点结束进程可终止
8. 启动项 Tab 可查看备份列表并恢复
