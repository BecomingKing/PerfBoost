# PerfBoost 打包分发指南

## 准备工作

- Python 3.9+ 已安装
- `pip install -r requirements.txt` 依赖就绪

## 打包步骤

### 1. 安装 PyInstaller

```bash
pip install pyinstaller
```

### 2. 打包为单文件 EXE

```bash
pyinstaller --onefile --windowed --name PerfBoost main.py
```

输出路径：`dist/PerfBoost.exe`，大小约 15-30 MB。

### 3. 打包为单目录（启动更快）

```bash
pyinstaller --onedir --windowed --name PerfBoost main.py
```

输出路径：`dist/PerfBoost/`，整个目录打包为 zip 分发。

### 4. 添加图标（可选）

准备一个 `.ico` 文件，然后：

```bash
pyinstaller --onefile --windowed --name PerfBoost --icon=assets/icon.ico main.py
```

## 数字签名

Windows 上无签名的 exe 会被 SmartScreen 拦截。获取签名证书后：

```bash
signtool sign /fd SHA256 /a /f certificate.pfx /p password dist/PerfBoost.exe
```

## 安装包制作（可选）

- **NSIS** — 免费，制作 Windows 标准安装向导
- **Inno Setup** — 免费，配置更简单
- **WiX Toolset** — 微软出品，功能最强但学习成本高

## 常见问题

**Q: 打包后杀软报毒？**
A: 参考 README.md 中的处理方式。

**Q: 打包后程序闪退？**
A: 尝试以 `--console` 模式打包查看错误日志：
```bash
pyinstaller --onefile --console --name PerfBoost main.py
./dist/PerfBoost.exe
```

**Q: 需要管理员权限？**
A: 部分功能（系统还原点、清理某些系统目录）需要管理员权限。可以右键 exe "以管理员身份运行"，或在打包时内嵌 manifest 文件自动提权。
