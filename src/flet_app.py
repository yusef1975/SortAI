import flet as ft
import os
import json
import threading
import time
import asyncio
from src.config import ConfigManager
from src.sorter import FileSorter
from src.watcher import FolderWatcher

# --- DESIGN TOKENS ---
ACCENT_BLUE = "#1978E5"
BG_LIGHT = "#F5F7FA"
CARD_WHITE = "#FFFFFF"
BORDER_RADIUS = 32
TEXT_PRIMARY = "#1A1C1E"
TEXT_SECONDARY = "#6C727A"

class SortAIFletApp:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.config = self.config_manager.config
        self.sorter = FileSorter(
            api_key=self.config.get("api_key", ""),
            model_name=self.config.get("model_name", "gemini/gemini-2.0-flash"),
            categories=self.config.get("categories", []),
            auto_categories=self.config.get("auto_categories", True)
        )
        self.watcher = None
        self.page = None

    async def breathe_animation(self):
        while True:
            if not self.page or not hasattr(self, 'status_card') or not self.status_card.shadow: break
            # Soft breathing blue glow
            for i in range(10, 30, 2):
                if not self.page: return
                self.status_card.shadow.blur_radius = i
                self.page.update()
                await asyncio.sleep(0.08)
            for i in range(30, 10, -2):
                if not self.page: return
                self.status_card.shadow.blur_radius = i
                self.page.update()
                await asyncio.sleep(0.08)

    async def main(self, page: ft.Page):
        self.page = page
        page.title = "SortAI Pro"
        page.theme_mode = ft.ThemeMode.LIGHT
        page.bgcolor = BG_LIGHT
        page.window.width = 1100
        page.window.height = 800
        page.padding = 0
        page.spacing = 0
        
        # UI Elements
        self.status_text = ft.Text("System Active", color=ACCENT_BLUE, size=24, weight=ft.FontWeight.W_700)
        self.history_list = ft.ListView(expand=1, spacing=15, padding=20)
        
        self.api_key_field = ft.TextField(
            label="Gemini API Key", 
            password=True, can_reveal_password=True, 
            value=self.config.get("api_key", ""), 
            border_radius=16, border_color="#E0E4E9",
            focused_border_color=ACCENT_BLUE,
            label_style=ft.TextStyle(color=TEXT_SECONDARY)
        )
        self.sources_field = ft.TextField(
            label="Watch Folders", 
            value=", ".join(self.config.get("source_folders", [])), 
            border_radius=16, border_color="#E0E4E9",
            focused_border_color=ACCENT_BLUE,
            label_style=ft.TextStyle(color=TEXT_SECONDARY)
        )
        self.target_field = ft.TextField(
            label="Target Root (Global)", 
            value=self.config.get("target_folder", ""), 
            border_radius=16, border_color="#E0E4E9",
            focused_border_color=ACCENT_BLUE,
            label_style=ft.TextStyle(color=TEXT_SECONDARY)
        )
        self.inplace_chk = ft.Checkbox(
            label="In-Place Organization", 
            value=self.config.get("inplace_organization", True),
            active_color=ACCENT_BLUE
        )

        # Sidebar
        self.rail = ft.Container(
            content=ft.Column([
                ft.Container(height=40),
                ft.IconButton(ft.Icons.HOME_ROUNDED, icon_color=ACCENT_BLUE, icon_size=28, on_click=lambda _: self.nav_to(0)),
                ft.IconButton(ft.Icons.TIMELINE_ROUNDED, icon_color=TEXT_SECONDARY, icon_size=28, on_click=lambda _: self.nav_to(1)),
                ft.IconButton(ft.Icons.SETTINGS_OUTLINED, icon_color=TEXT_SECONDARY, icon_size=28, on_click=lambda _: self.nav_to(2)),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            width=80,
            bgcolor=CARD_WHITE,
            border=ft.border.only(right=ft.border.BorderSide(1, "#E0E4E9"))
        )

        # Dashboard View
        self.status_card = ft.Container(
            content=ft.Column([
                ft.Text("DASHBOARD", weight="bold", color=TEXT_SECONDARY, size=12),
                self.status_text,
                ft.Text("AI Real-time File Surveillance", size=11, color=TEXT_SECONDARY),
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=CARD_WHITE,
            padding=30,
            border_radius=BORDER_RADIUS,
            shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.with_opacity(0.1, ACCENT_BLUE)),
            col={"sm": 12, "md": 8},
            height=250,
        )

        self.scan_btn = ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Icon(ft.Icons.AUTO_AWESOME_ROUNDED, color=ACCENT_BLUE, size=32),
                    padding=20, border_radius=50, bgcolor=ft.Colors.with_opacity(0.1, ACCENT_BLUE)
                ),
                ft.Container(height=10),
                ft.Text("MANUAL SCAN", weight="bold", size=14, color=ACCENT_BLUE),
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            on_click=self.start_manual_scan,
            bgcolor=ft.Colors.with_opacity(0.6, CARD_WHITE),
            border_radius=BORDER_RADIUS,
            border=ft.border.all(1, ft.Colors.with_opacity(0.4, "white")),
            blur=ft.Blur(10, 10),
            col={"sm": 12, "md": 4},
            height=250,
        )

        self.dashboard_view = ft.Container(
            content=ft.Column([
                ft.ResponsiveRow([
                    self.status_card, self.scan_btn,
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.BOLT_ROUNDED, color="#FFA000"),
                            ft.Text("PRO AI ENGINE ENGAGED", weight="bold", size=12, color=TEXT_PRIMARY)
                        ], alignment=ft.MainAxisAlignment.CENTER),
                        bgcolor=CARD_WHITE, border_radius=BORDER_RADIUS, col={"lg": 12}, height=100,
                        shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.05, "black"))
                    )
                ], spacing=20, run_spacing=20),
            ], scroll=ft.ScrollMode.AUTO),
            padding=40, expand=True
        )

        self.main_area = ft.Container(content=self.dashboard_view, expand=True)

        page.add(ft.Row([self.rail, self.main_area], expand=True, spacing=0))

        asyncio.create_task(self.breathe_animation())
        self.refresh_history()
        if self.config.get("source_folders"): self.start_watcher_logic()

    def nav_to(self, idx):
        # UI Refresh for Sidebar
        for i, control in enumerate(self.rail.content.controls[1:4]):
            control.icon_color = ACCENT_BLUE if i == idx else TEXT_SECONDARY
        
        if idx == 0: self.main_area.content = self.dashboard_view
        elif idx == 1: self.main_area.content = self.create_history_view()
        elif idx == 2: self.main_area.content = self.create_settings_view()
        self.page.update()

    def create_history_view(self):
        return ft.Container(
            content=ft.Column([
                ft.Text("History", size=32, weight="bold", color=TEXT_PRIMARY),
                ft.Container(self.history_list, expand=True, bgcolor=CARD_WHITE, border_radius=BORDER_RADIUS, shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.05, "black"))),
                ft.ElevatedButton("Undo Last Action", icon=ft.Icons.UNDO, bgcolor=ACCENT_BLUE, color="white", on_click=self.undo_last, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)))
            ], spacing=20),
            padding=40, expand=True
        )

    def create_settings_view(self):
        return ft.Container(
            content=ft.Column([
                ft.Text("Settings", size=32, weight="bold", color=TEXT_PRIMARY),
                ft.Container(
                    content=ft.Column([
                        self.api_key_field, self.sources_field, self.target_field, self.inplace_chk
                    ], spacing=20),
                    padding=30, bgcolor=CARD_WHITE, border_radius=BORDER_RADIUS,
                    shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.05, "black"))
                ),
                ft.ElevatedButton("Save Preferences", icon=ft.Icons.SAVE, bgcolor=ACCENT_BLUE, color="white", on_click=self.save_settings, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)))
            ], spacing=20, scroll=ft.ScrollMode.AUTO),
            padding=40, expand=True
        )

    def refresh_history(self):
        self.history_list.controls.clear()
        if os.path.exists("history.json"):
            try:
                with open("history.json", "r") as f:
                    history = json.load(f)
                    for entry in history:
                        self.history_list.controls.append(
                            ft.Container(
                                content=ft.ListTile(
                                    leading=ft.Icon(ft.Icons.FILE_COPY_ROUNDED, color=ACCENT_BLUE),
                                    title=ft.Text(entry['filename'], size=14, weight="bold", color=TEXT_PRIMARY),
                                    subtitle=ft.Text(f"Organized into {entry['category']}", size=12, color=TEXT_SECONDARY),
                                ),
                                bgcolor=CARD_WHITE, border_radius=16, border=ft.border.all(1, "#F0F2F5")
                            )
                        )
            except: pass
        if self.page: self.page.update()

    def start_manual_scan(self, e):
        sources = self.config.get("source_folders", [])
        target = self.config.get("target_folder")
        inplace = self.config.get("inplace_organization", True)
        
        def run():
            if not sources: return
            self.status_text.value = "Scanning..."
            self.page.update()
            for s in sources:
                if os.path.exists(s):
                    files = [f for f in os.listdir(s) if os.path.isfile(os.path.join(s, f))]
                    for f in files:
                        self.sorter.organize_file(os.path.join(s, f), s if inplace else target)
                        self.refresh_history()
            self.status_text.value = "Scan Complete"
            self.page.update()
            time.sleep(2)
            self.status_text.value = "System Active"
            self.page.update()
        
        threading.Thread(target=run, daemon=True).start()

    def save_settings(self, e):
        api_key = self.api_key_field.value.strip()
        sources = [s.strip() for s in self.sources_field.value.split(",") if s.strip()]
        target = self.target_field.value.strip()
        inplace = self.inplace_chk.value
        
        self.config_manager.set("api_key", api_key)
        self.config_manager.set("source_folders", sources)
        self.config_manager.set("target_folder", target)
        self.config_manager.set("inplace_organization", inplace)
        
        self.sorter.api_key = api_key
        self.start_watcher_logic()
        self.page.snack_bar = ft.SnackBar(ft.Text("Preferences Saved Successfully"))
        self.page.snack_bar.open = True
        self.page.update()

    def undo_last(self, e):
        if os.path.exists("history.json"):
            with open("history.json", 'r') as f:
                history = json.load(f)
            if history:
                if self.sorter.undo_move(history[0]):
                    history.pop(0)
                    with open("history.json", 'w') as f:
                        json.dump(history, f, indent=4)
                    self.refresh_history()
                    self.page.snack_bar = ft.SnackBar(ft.Text("Action Undone"))
                    self.page.snack_bar.open = True
                    self.page.update()

    def start_watcher_logic(self):
        if self.watcher: self.watcher.stop()
        sources = self.config.get("source_folders", [])
        target = self.config.get("target_folder")
        inplace = self.config.get("inplace_organization", True)
        if sources:
            self.watcher = FolderWatcher(sources, target, self.sorter, on_move_callback=self.refresh_history, inplace=inplace)
            self.watcher.start()
            self.status_text.value = "Surveillance On"
            if self.page: self.page.update()

if __name__ == "__main__":
    app = SortAIFletApp()
    ft.app(target=app.main)
