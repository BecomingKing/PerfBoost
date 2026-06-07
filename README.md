<p align="center">
  <img src="assets/logo.png" alt="PerfBoost" width="120" />
</p>

<h1 align="center">⚡ PerfBoost</h1>

<p align="center">
  <strong>轻量级 Windows 系统性能优化工具箱 — 让电脑回归流畅</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="Python 3.9+" />
  <img src="https://img.shields.io/badge/platform-Windows%2010%2F11-0078D6.svg" alt="Windows" />
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License MIT" />
  <img src="https://img.shields.io/badge/ui-CustomTkinter-3498db.svg" alt="UI" />
</p>

<p align="center">
  <img src="assets/screenshots/dashboard.png" alt="仪表盘" width="45%" />
  &nbsp;&nbsp;
  <img src="assets/screenshots/cleaner.png" alt="清理" width="45%" />
</p>

---

## 这是什么？

PerfBoost 是一款面向普通用户的 Windows 系统优化工具。它把你平时需要到处找的「清理垃圾」「管理开机启动」「查看谁在吃内存」等操作整合到一个干净的界面里，**没有广告、没有捆绑、代码完全开源**。

和 CCleaner、腾讯管家等商业软件不同，PerfBoost 不做「玄学优化」——每一项操作都有清晰的说明，让你知道它在做什么、会不会有风险。

## ✨ 功能

| 模块 | 说明 |
|------|------|
| 📊 **仪表盘** | CPU / 内存 / 磁盘 / 网络实时监控；**一句话诊断**告诉你电脑当前健康状态（如「C 盘剩余 3.2 GB，建议清理」）；开机时长统计 |
| 🧹 **垃圾清理** | 扫描系统临时文件、浏览器缓存等垃圾；**风险分级**（🟢安全 / 🟡谨慎 / 🔴高级）+ 文件预览；安全项默认勾选；被占用的文件标记为「重启后自动删除」；统计累计清理总量 |
| 🚀 **启动项管理** | 列出所有开机自启程序，显示**开机耗时预估**和**影响评估**；自动过滤已卸载软件的残留项；一键禁用/恢复，禁用前备份支持复原 |
| 📋 **进程管理** | 进程列表 + 内存可视化条；搜索过滤；系统关键进程受保护（🔒标记，不可终止）；右键菜单支持结束进程和打开文件位置 |
| ⚙️ **设置** | 暗色/亮色/跟随系统主题切换；关于页面 |

## 🎯 为什么选择 PerfBoost？

| | PerfBoost | CCleaner | 360 / 腾讯管家 |
|---|---|---|---|
| **开源** | ✅ 完全开源 | ❌ 闭源 | ❌ 闭源 |
| **无广告** | ✅ 纯净 | ❌ 免费版有广告 | ❌ 大量推广 |
| **无捆绑** | ✅ 独立运行 | ⚠️ 安装器带捆绑 | ❌ 全家桶 |
| **操作透明** | ✅ 每项操作都有白话解释 | ⚠️ 部分操作模糊 | ❌ 「一键优化」黑盒 |
| **轻量** | ✅ ~30MB 单文件 | ⚠️ ~50MB | ❌ 数百MB |
| **风险标记** | ✅ 清理项标注安全/谨慎/危险 | ❌ 无 | ❌ 无 |

## 📦 安装

### 方式一：下载 EXE（推荐普通用户）

从 [Releases](https://github.com/BecomingKing/perfboost/releases) 页面下载 `PerfBoost.exe`，双击运行即可，无需安装 Python。

> ⚠️ **杀软误报说明**：PyInstaller 打包的 exe 可能被 Windows Defender 或杀毒软件误报。这是因为没有数字签名（代码签名证书约 ¥300-1000/年）。如遇误报，可选择「仍要运行」或将文件目录加入杀软信任区。介意的话请使用方式二。

### 方式二：源码运行（推荐开发者 / 介意误报的用户）

```bash
# 1. 克隆仓库
git clone https://github.com/BecomingKing/perfboost.git
cd perfboost

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行
python main.py
```

**要求**：Python 3.9+，Windows 10 或 Windows 11。

### 管理员权限

部分功能（清理系统临时目录、某些受保护的缓存）需要管理员权限。程序会在需要时弹出提示，你可以选择：
- **以管理员身份重启** PerfBoost
- **跳过需要权限的项目**，只清理不需要权限的

## 🖥 项目结构

```
perfboost/
├── main.py              # 入口：单实例锁 + 启动
├── app.py               # 主窗口：侧边栏导航 + 页面切换 + 监控轮询
├── requirements.txt     # Python 依赖
├── ui/                  # 界面层（CustomTkinter）
│   ├── dashboard.py     #   仪表盘 — 4 卡片 + 一句话诊断
│   ├── cleaner.py       #   清理 — 风险标记 + 文件预览
│   ├── startup.py       #   启动项 — 开机耗时 + 影响评估
│   ├── process.py       #   进程 — 内存条 + 受保护标记
│   └── settings.py      #   设置 — 主题切换
├── core/                # 核心逻辑层（无 GUI 依赖）
│   ├── monitor.py       #   系统监控（psutil 采样）
│   ├── cleaner.py       #   清理引擎（扫描 + 删除 + 重启后清理）
│   ├── startup.py       #   启动项读写（注册表 + 启动文件夹）
│   ├── process.py       #   进程管理（受保护列表 + 终止）
│   └── tray.py          #   系统托盘（最小化到托盘 + 状态提示）
├── utils/               # 工具层
│   ├── config.py        #   配置持久化（JSON，自动合并默认值）
│   └── helpers.py       #   通用函数（格式化、权限检测、路径安全判断）
├── data/                # 运行时数据（配置、锁文件）— 已 gitignore
├── assets/              # 资源文件（图标、截图）
└── tests/               # 单元测试
```

## 🛠 开发

### 运行测试

```bash
pytest tests/ -v
```

### 打包为 EXE

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name PerfBoost main.py
```

输出在 `dist/PerfBoost.exe`。详见 [BUILD.md](BUILD.md)。

### 技术栈

- **[CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)** — 现代化的 Tkinter 主题层
- **[psutil](https://github.com/giampaolo/psutil)** — 系统资源监控
- **[pystray](https://github.com/moses-palmer/pystray)** — 系统托盘
- **[Pillow](https://python-pillow.org/)** — 托盘图标处理

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

- 🐛 发现 bug？请在 Issue 中附上截图和复现步骤
- 💡 有新功能想法？先开 Issue 讨论再写代码
- 🔧 贡献代码？请确保 `pytest tests/ -v` 全部通过

## 📄 许可证

MIT License — 详见 [LICENSE](LICENSE) 文件。

简单说：你可以自由使用、修改、分发，甚至用于商业用途，只需保留版权声明。

---

<p align="center">
  <sub>Made with ❤️ for Windows users</sub>
</p>
