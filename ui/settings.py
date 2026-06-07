"""设置页面：外观 + 关于."""

import customtkinter as ctk

from utils.config import Config


class SettingsFrame(ctk.CTkFrame):
    def __init__(self, master, config: Config, on_theme_change=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.config = config
        self._on_theme_change = on_theme_change
        self._build_ui()

    def _build_ui(self):
        ctk.CTkLabel(
            self, text="设置",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(anchor="w", padx=20, pady=(15, 15))

        # ---- 外观 ----
        appearance_card = ctk.CTkFrame(self, corner_radius=10)
        appearance_card.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(appearance_card, text="外观",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=14, pady=(12, 8))

        current_theme = self.config.get("theme", "system")
        self.theme_var = ctk.StringVar(value=current_theme)

        radio_frame = ctk.CTkFrame(appearance_card, fg_color="transparent")
        radio_frame.pack(fill="x", padx=14, pady=(0, 12))

        for value, label in [("system", "跟随系统"), ("dark", "暗色"), ("light", "亮色")]:
            ctk.CTkRadioButton(
                radio_frame, text=label, variable=self.theme_var, value=value,
                command=self._on_theme_changed,
            ).pack(side="left", padx=(0, 20), pady=4)

        # ---- 关于 ----
        about_card = ctk.CTkFrame(self, corner_radius=10)
        about_card.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(about_card, text="关于",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=14, pady=(12, 8))

        from main import __version__
        ctk.CTkLabel(about_card, text=f"PerfBoost  v{__version__}",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=14)
        ctk.CTkLabel(about_card, text="Windows 系统性能优化工具",
                     font=ctk.CTkFont(size=12), text_color="gray60").pack(anchor="w", padx=14, pady=(2, 12))

    def _on_theme_changed(self):
        theme = self.theme_var.get()
        self.config.set("theme", theme)
        if self._on_theme_change:
            self._on_theme_change(theme)
