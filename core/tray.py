"""系统托盘模块：最小化到托盘、右键菜单、资源异常告警."""

import threading
import time
import queue

try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False


# 图标配色
COLORS = {
    "normal": "#1a5276",   # 深蓝 — 正常运行
    "warn":   "#e67e22",   # 橙色 — CPU>80% 或 内存>85%
    "danger": "#e74c3c",   # 红色 — CPU>90% 或 内存>90%
}


class SystemTray:
    """系统托盘管理器."""

    def __init__(self, on_show, on_hide, on_exit, monitor=None):
        self._on_show = on_show    # 显示窗口回调
        self._on_hide = on_hide    # 隐藏到托盘回调
        self._on_exit = on_exit    # 退出回调
        self._monitor = monitor
        self._tray = None  # type: ignore
        self._alert_running = False
        self._last_alert_time = 0
        self._current_color = ""   # 当前图标颜色，避免重复更新

    def is_available(self) -> bool:
        return TRAY_AVAILABLE

    def start(self) -> None:
        if not TRAY_AVAILABLE:
            return
        image = self._create_icon(COLORS["normal"])
        menu = self._build_menu()
        self._tray = pystray.Icon("perfboost", image, "PerfBoost", menu)
        threading.Thread(target=self._tray.run, daemon=True).start()
        # 启动资源告警
        if self._monitor:
            self._alert_running = True
            threading.Thread(target=self._alert_loop, daemon=True).start()

    def stop(self) -> None:
        self._alert_running = False
        if self._tray:
            self._tray.stop()

    def notify(self, title: str, message: str) -> None:
        """弹出气泡通知."""
        if self._tray:
            self._tray.notify(message, title)

    def update_status(self, cpu: float, mem: float) -> None:
        """公开方法：更新托盘图标颜色和 tooltip（由 app.py 轮询调用）."""
        if not self._tray:
            return

        # 判断颜色
        if cpu > 90 or mem > 90:
            color = COLORS["danger"]
        elif cpu > 80 or mem > 85:
            color = COLORS["warn"]
        else:
            color = COLORS["normal"]

        # 更新 tooltip（每次更新，成本极低）
        self._tray.title = f"PerfBoost — CPU: {cpu:.0f}% | 内存: {mem:.0f}%"

        # 只在颜色变化时更换图标和菜单
        if color != self._current_color:
            self._current_color = color
            self._tray.icon = self._create_icon(color)
            self._tray.update_menu()

    # ---- 菜单 ----

    def _build_menu(self):
        """构建右键菜单（含顶部状态行）."""
        cpu_str = f"CPU: --"
        mem_str = f"内存: --"
        status_text = f"📊 {cpu_str} | {mem_str}"
        return pystray.Menu(
            pystray.MenuItem(status_text, None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("显示窗口", self._show_window, default=True),
            pystray.MenuItem("隐藏窗口", self._hide_window),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("退出", self._quit),
        )

    def _show_window(self) -> None:
        self._on_show()

    def _hide_window(self) -> None:
        self._on_hide()

    def _quit(self) -> None:
        self._alert_running = False
        if self._tray:
            self._tray.stop()
        self._on_exit()  # 真正退出

    # ---- 资源告警 ----

    def _alert_loop(self) -> None:
        """后台监控资源使用，超阈值时弹通知."""
        while self._alert_running:
            try:
                data = self._monitor.data_queue.get(timeout=2)
                if "error" in data:
                    continue
                cpu = data.get("cpu_percent", 0)
                mem = data.get("memory_percent", 0)
                now = time.time()
                if (cpu > 90 or mem > 90) and (now - self._last_alert_time > 300):
                    self._last_alert_time = now
                    msg_parts = []
                    if cpu > 90:
                        msg_parts.append(f"CPU: {cpu:.0f}%")
                    if mem > 90:
                        msg_parts.append(f"内存: {mem:.0f}%")
                    self.notify("⚠️ 系统资源异常", "\\n".join(msg_parts))
            except queue.Empty:
                continue
            except Exception:
                break

    # ---- 图标绘制 ----

    @staticmethod
    def _create_icon(base_color: str) -> "Image.Image":
        """绘制 64x64 图标：圆角矩形背景 + 白色多边形闪电."""
        size = 64
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # 圆角矩形背景（用圆角矩形近似）
        margin = 4
        r = 12  # 圆角半径
        draw.rounded_rectangle(
            [margin, margin, size - margin, size - margin],
            radius=r, fill=base_color,
        )

        # 白色闪电符号（polygon 绘制）
        bolt_color = "white"
        # 闪电形状：上窄下宽的折线多边形
        bolt = [
            (28, 10),   # 顶部中点
            (18, 32),   # 左侧内折
            (26, 32),   # 中部横梁上
            (22, 52),   # 底部尖端偏左
            (38, 28),   # 右侧内折
            (30, 28),   # 中部横梁下
            (36, 10),   # 回到顶部
        ]
        draw.polygon(bolt, fill=bolt_color)

        return img
