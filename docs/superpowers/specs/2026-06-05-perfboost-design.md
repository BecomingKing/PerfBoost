# PerfBoost - Windows 系统性能优化工具 设计文档

> 日期: 2026-06-05 | 状态: 待评审

## 1. 概述

PerfBoost 是一个 Windows 桌面系统性能优化工具，提供硬件监控、垃圾清理、启动项管理和进程管理四大模块。目标用户为普通 PC 用户，追求"一键式"操作体验。

## 2. 技术选型

| 项目 | 选择 | 理由 |
|------|------|------|
| 语言 | Python 3.11+ | AI 代码生成质量最高，库生态丰富 |
| GUI | CustomTkinter | 现代化暗色主题、AI 熟悉、代码简洁、打包方便 |
| 系统监控 | psutil | Python 事实标准，支持 CPU/内存/磁盘/进程 |
| 注册表操作 | winreg (标准库) | 启动项读写 |
| 打包 | PyInstaller | 单 exe 分发 |

## 3. 架构

采用**单体多线程架构**，分层为 UI → Core → Utils：

```
perfboost/
├── main.py              # 入口，初始化 App
├── app.py               # CustomTkinter 主窗口 + Tab 管理
├── ui/                   # UI 层（纯展示 + 事件绑定）
│   ├── dashboard.py     # 仪表盘 Tab
│   ├── cleaner.py       # 清理 Tab
│   ├── startup.py       # 启动项 Tab
│   └── process.py       # 进程 Tab
├── core/                 # 核心逻辑层（不依赖 UI）
│   ├── monitor.py       # 硬件监控（psutil 封装）
│   ├── cleaner.py       # 垃圾清理引擎
│   ├── startup.py       # 启动项读写
│   └── process.py       # 进程管理
├── utils/                # 工具层
│   ├── config.py        # 配置读写（JSON）
│   └── helpers.py       # 通用函数（格式化字节、权限检查等）
└── assets/               # 图标/资源文件
```

**数据流：** 监控线程(psutil) → 采样队列 → UI 定时器轮询 → 组件更新

## 4. 模块设计

### 4.1 仪表盘 (Dashboard)

**UI 布局：**
- 第一行：CPU 使用率（环状进度） + 内存使用率（环状进度）
- 第二行：磁盘分区使用情况（横向进度条，自动发现所有固定磁盘）
- 第三行：CPU 温度 + 网络速率（上传/下载）
- 底部：优化统计摘要（上次优化时间、已清理量、已禁用启动项数）

**核心逻辑：**
- 后台线程每 1 秒采样 psutil，通过 `queue.Queue` 推送数据
- UI 定时器每 1 秒消费队列，更新组件
- 温度读取使用 `psutil.sensors_temperatures()`，不支持时隐藏温度卡片
- 网络速率需要计算两次采样差值

### 4.2 垃圾清理 (Cleaner)

**扫描类别：**

| 类别 | 路径 | 默认勾选 |
|------|------|---------|
| Windows 临时文件 | `%TEMP%`, `C:\Windows\Temp` | ✅ |
| 浏览器缓存 | Chrome/Edge/Firefox Cache | ✅ |
| 回收站 | Shell API | ✅ |
| 系统日志 | Windows Event Logs 备份 | ❌ |
| 缩略图缓存 | `thumbcache_*.db` | ❌ |

**安全约束：**
- 白名单模式：只扫描明确可删的文件类型和目录
- 不碰 System32、驱动目录、注册表 HIVE 文件
- 删除前验证路径是否在允许范围内

**流程：** 扫描（计算大小） → 分类展示 → 勾选确认 → 清理（带进度条）

### 4.3 启动项管理 (Startup)

**数据来源：**
- `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`
- `HKLM\Software\Microsoft\Windows\CurrentVersion\Run`
- 启动文件夹 `shell:startup`（当前用户 + 公共）
- 任务计划读取（只读展示，不修改）

**功能：** 列表展示 → 每行有启用/禁用开关 → 实时生效

### 4.4 进程管理 (Process)

**列表字段：** 名称、PID、CPU%、内存(MB)、磁盘 IO(MB/s)

**功能：**
- 默认按内存降序排列
- 搜索/过滤进程名
- 结束进程（确认弹窗，保护系统关键进程）
- 右键菜单：打开文件位置、在线搜索进程信息

## 5. 配置持久化

`%APPDATA%/PerfBoost/config.json`:
```json
{
  "clean_categories": { "temp": true, "browser_cache": true, ... },
  "monitor_interval": 1,
  "temperature_unit": "celsius",
  "startup_disabled": ["path/to/program1", "..."],
  "last_optimization": "2026-06-05T14:30:00",
  "total_cleaned_bytes": 2469606195
}
```

## 6. 错误处理策略

- 权限不足的目录：跳过并记录，不中断扫描
- 文件被占用：跳过当前文件，继续清理其余
- 温度不可用：隐藏对应卡片，不弹错误
- 所有后台线程异常：`queue` 传递错误信息，UI 以 toast 形式展示

## 7. 未包含（YAGNI，留给 v2）

- 网络流量详细分析
- 驱动更新检测
- 定时自动优化
- 系统快照对比
- 暗色/亮色主题切换（首版固定暗色）
- 国际化
