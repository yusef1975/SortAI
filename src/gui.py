import customtkinter as ctk
import pystray
from PIL import Image, ImageDraw
import threading
import sys
import os
import json
import time
from tkinter import messagebox, filedialog
from src.config import ConfigManager
from src.sorter import FileSorter
from src.watcher import FolderWatcher
from plyer import notification
import winreg as reg

class SortAIApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Classic Dark Theme
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        
        self.config_manager = ConfigManager()
        self.config = self.config_manager.config

        self.sorter = FileSorter(
            api_key=self.config.get("api_key", ""),
            openai_key=self.config.get("openai_api_key", ""),
            anthropic_key=self.config.get("anthropic_api_key", ""),
            local_base_url=self.config.get("local_base_url", ""),
            model_name=self.config.get("model_name", "gemini/gemini-2.0-flash"),
            categories=self.config.get("categories", []),
            auto_categories=self.config.get("auto_categories", True)
        )
        self.watcher = None
        
        self.setup_ui()
        self.setup_tray()
        
        if self.config.get("source_folders") and (self.config.get("target_folder") or self.config.get("inplace_organization")):
            self.start_watcher()

    def setup_ui(self):
        self.title("SortAI Pro")
        self.geometry("900x650")

        # Top TabView
        self.tabview = ctk.CTkTabview(self, height=550)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.tab_dashboard = self.tabview.add("Dashboard")
        self.tab_history = self.tabview.add("History")
        self.tab_rules = self.tabview.add("Rules")
        self.tab_settings = self.tabview.add("Settings")

        self.setup_dashboard_tab()
        self.setup_history_tab()
        self.setup_rules_tab()
        self.setup_settings_tab()

    def setup_dashboard_tab(self):
        self.tab_dashboard.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self.tab_dashboard, text="System Status", font=("Inter", 24, "bold")).grid(row=0, column=0, pady=20)
        
        self.status_indicator = ctk.CTkLabel(self.tab_dashboard, text="● SYSTEM IDLE", text_color="gray", font=("Consolas", 16))
        self.status_indicator.grid(row=1, column=0, pady=10)
        
        self.watch_info = ctk.CTkLabel(self.tab_dashboard, text="Awaiting Configuration")
        self.watch_info.grid(row=2, column=0, pady=10)

        self.btn_scan = ctk.CTkButton(self.tab_dashboard, text="Run Manual Scan", command=self.scan_existing_files)
        self.btn_scan.grid(row=3, column=0, pady=20)

    def setup_history_tab(self):
        self.tab_history.grid_columnconfigure(0, weight=1)
        self.tab_history.grid_rowconfigure(0, weight=1)
        self.history_list = ctk.CTkTextbox(self.tab_history, state="disabled")
        self.history_list.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        btn_frame = ctk.CTkFrame(self.tab_history, fg_color="transparent")
        btn_frame.grid(row=1, column=0, pady=10)
        self.btn_undo = ctk.CTkButton(btn_frame, text="Undo Last Move", command=self.undo_last_move, fg_color="red", hover_color="darkred")
        self.btn_undo.pack(side="left", padx=10)
        self.refresh_history()

    def setup_rules_tab(self):
        self.tab_rules.grid_columnconfigure(1, weight=1)
        self.auto_cat_var = ctk.BooleanVar(value=self.config.get("auto_categories", True))
        ctk.CTkCheckBox(self.tab_rules, text="Auto AI Categorization", variable=self.auto_cat_var, command=self.toggle_auto_cat).grid(row=0, column=0, columnspan=2, padx=20, pady=20, sticky="w")
        
        ctk.CTkLabel(self.tab_rules, text="Manual Categories:").grid(row=1, column=0, padx=20, pady=10, sticky="w")
        self.cat_entry = ctk.CTkEntry(self.tab_rules)
        self.cat_entry.grid(row=1, column=1, padx=20, pady=10, sticky="ew")
        self.cat_entry.insert(0, ", ".join(self.config.get("categories", [])))
        if self.auto_cat_var.get(): self.cat_entry.configure(state="disabled")

    def setup_settings_tab(self):
        self.tab_settings.grid_columnconfigure(1, weight=1)
        
        # Provider Selection
        ctk.CTkLabel(self.tab_settings, text="AI Company:", font=("Inter", 12, "bold")).grid(row=0, column=0, padx=20, pady=15, sticky="w")
        self.provider_combo = ctk.CTkComboBox(self.tab_settings, values=["Gemini", "OpenAI", "Anthropic", "Local"], command=self.on_provider_change)
        self.provider_combo.grid(row=0, column=1, padx=20, pady=15, sticky="ew")
        self.provider_combo.set(self.config.get("active_provider", "Gemini").capitalize())

        # API Key Container (Dynamic)
        self.key_container = ctk.CTkFrame(self.tab_settings, fg_color="transparent")
        self.key_container.grid(row=1, column=0, columnspan=2, sticky="ew")
        self.key_container.grid_columnconfigure(1, weight=1)

        self.setup_provider_fields()

        # Model Selection
        ctk.CTkLabel(self.tab_settings, text="AI Model:", font=("Inter", 12, "bold")).grid(row=2, column=0, padx=20, pady=10, sticky="w")
        self.model_combo = ctk.CTkComboBox(self.tab_settings, values=[])
        self.model_combo.grid(row=2, column=1, padx=20, pady=10, sticky="ew")
        
        # Other Settings
        ctk.CTkLabel(self.tab_settings, text="Watch Folders:", font=("Inter", 12, "bold")).grid(row=3, column=0, padx=20, pady=10, sticky="w")
        self.folders_entry = ctk.CTkEntry(self.tab_settings)
        self.folders_entry.grid(row=3, column=1, padx=20, pady=10, sticky="ew")
        self.folders_entry.insert(0, ", ".join(self.config.get("source_folders", [])))
        ctk.CTkButton(self.tab_settings, text="Add Folder", command=self.add_source_folder).grid(row=3, column=2, padx=10)

        ctk.CTkLabel(self.tab_settings, text="Organized Root:", font=("Inter", 12, "bold")).grid(row=4, column=0, padx=20, pady=10, sticky="w")
        self.target_entry = ctk.CTkEntry(self.tab_settings)
        self.target_entry.grid(row=4, column=1, padx=20, pady=10, sticky="ew")
        self.target_entry.insert(0, self.config.get("target_folder", ""))
        self.btn_browse_target = ctk.CTkButton(self.tab_settings, text="Browse", command=self.browse_target)
        self.btn_browse_target.grid(row=4, column=2, padx=10)

        self.inplace_var = ctk.BooleanVar(value=self.config.get("inplace_organization", True))
        ctk.CTkCheckBox(self.tab_settings, text="Organize In-Place (Original folder)", 
                        variable=self.inplace_var, command=self.update_ui_states).grid(row=5, column=0, columnspan=2, padx=20, pady=5, sticky="w")

        self.auto_start_var = ctk.BooleanVar(value=self.config.get("auto_start", False))
        ctk.CTkCheckBox(self.tab_settings, text="Start with Windows", variable=self.auto_start_var).grid(row=6, column=0, columnspan=2, padx=20, pady=5, sticky="w")

        ctk.CTkButton(self, text="Save Settings & Restart", command=self.save_pro_settings).pack(pady=20)
        
        self.on_provider_change(self.provider_combo.get())
        self.model_combo.set(self.config.get("model_name", "gemini/gemini-2.0-flash"))
        self.update_ui_states()

    def setup_provider_fields(self):
        # We'll create all entries once and hide/show them
        self.api_key_label = ctk.CTkLabel(self.key_container, text="API Key:", font=("Inter", 12, "bold"))
        self.api_key_entry = ctk.CTkEntry(self.key_container, show="*", placeholder_text="Enter Key")
        
        self.local_url_label = ctk.CTkLabel(self.key_container, text="Base URL:", font=("Inter", 12, "bold"))
        self.local_url_entry = ctk.CTkEntry(self.key_container, placeholder_text="http://localhost:11434/v1")

    def on_provider_change(self, provider):
        # Hide everything in key_container first
        for child in self.key_container.winfo_children():
            child.grid_forget()

        models = {
            "Gemini": ["gemini/gemini-2.0-flash", "gemini/gemini-1.5-pro", "gemini/gemini-1.5-flash"],
            "OpenAI": ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
            "Anthropic": ["claude-3-5-sonnet-20240620", "claude-3-opus-20240229", "claude-3-haiku-20240307"],
            "Local": ["ollama/llama3", "ollama/mistral", "custom/local"]
        }

        self.model_combo.configure(values=models.get(provider, []))
        if models.get(provider):
            self.model_combo.set(models[provider][0])

        if provider == "Local":
            self.local_url_label.grid(row=0, column=0, padx=20, pady=5, sticky="w")
            self.local_url_entry.grid(row=0, column=1, padx=20, pady=5, sticky="ew")
            self.local_url_entry.delete(0, "end")
            self.local_url_entry.insert(0, self.config.get("local_base_url", "http://localhost:11434/v1"))
        else:
            self.api_key_label.grid(row=0, column=0, padx=20, pady=5, sticky="w")
            self.api_key_entry.grid(row=0, column=1, padx=20, pady=5, sticky="ew")
            self.api_key_entry.delete(0, "end")
            
            key_map = {"Gemini": "api_key", "OpenAI": "openai_api_key", "Anthropic": "anthropic_api_key"}
            self.api_key_entry.insert(0, self.config.get(key_map.get(provider), ""))

    def update_ui_states(self):
        if self.inplace_var.get():
            self.target_entry.configure(state="disabled")
            self.btn_browse_target.configure(state="disabled")
        else:
            self.target_entry.configure(state="normal")
            self.btn_browse_target.configure(state="normal")

    def toggle_auto_cat(self):
        self.cat_entry.configure(state="disabled" if self.auto_cat_var.get() else "normal")

    def add_source_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            current = self.folders_entry.get().strip()
            self.folders_entry.delete(0, "end")
            self.folders_entry.insert(0, f"{current}, {folder}" if current else folder)

    def browse_target(self):
        folder = filedialog.askdirectory()
        if folder:
            self.target_entry.delete(0, "end")
            self.target_entry.insert(0, folder)

    def save_pro_settings(self):
        provider = self.provider_combo.get()
        model_name = self.model_combo.get().strip()
        
        if provider == "Local":
            self.config_manager.set("local_base_url", self.local_url_entry.get().strip())
        else:
            key_map = {"Gemini": "api_key", "OpenAI": "openai_api_key", "Anthropic": "anthropic_api_key"}
            self.config_manager.set(key_map.get(provider), self.api_key_entry.get().strip())

        sources = [s.strip() for s in self.folders_entry.get().split(",") if s.strip()]
        target = self.target_entry.get().strip()
        
        self.config_manager.set("active_provider", provider.lower())
        self.config_manager.set("model_name", model_name)
        self.config_manager.set("source_folders", sources)
        self.config_manager.set("target_folder", target)
        self.config_manager.set("auto_start", self.auto_start_var.get())
        self.config_manager.set("inplace_organization", self.inplace_var.get())
        
        self.set_auto_start(self.auto_start_var.get())
        
        # Load all keys for sorter
        self.sorter.update_config(
            self.config.get("api_key", ""),
            self.config.get("openai_api_key", ""),
            self.config.get("anthropic_api_key", ""),
            self.config.get("local_base_url", ""),
            model_name,
            self.config.get("categories", []),
            self.config.get("auto_categories", True)
        )
        self.start_watcher()
        messagebox.showinfo("Success", "Settings persistent.")

    def set_auto_start(self, enabled):
        try:
            key = reg.OpenKey(reg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Run', 0, reg.KEY_SET_VALUE)
            if enabled: reg.SetValueEx(key, "SortAI", 0, reg.REG_SZ, f'"{sys.executable}" "{os.path.abspath(sys.argv[0])}"')
            else:
                try: reg.DeleteValue(key, "SortAI")
                except: pass
            reg.CloseKey(key)
        except: pass

    def start_watcher(self):
        if self.watcher: self.watcher.stop()
        sources = self.config.get("source_folders", [])
        target = self.config.get("target_folder")
        inplace = self.config.get("inplace_organization", True)
        if sources:
            self.watcher = FolderWatcher(sources, target, self.sorter, on_move_callback=self.notify_user_move, inplace=inplace)
            self.watcher.start()
            self.status_indicator.configure(text="● SYSTEM ACTIVE", text_color="green")
            self.watch_info.configure(text=f"Monitoring {len(sources)} folders")

    def notify_user_move(self):
        self.after(0, self.refresh_history)
        try: notification.notify(title="SortAI Pro", message="File organized.", timeout=3)
        except: pass

    def refresh_history(self):
        self.history_list.configure(state="normal")
        self.history_list.delete("1.0", "end")
        if os.path.exists("history.json"):
            with open("history.json", 'r') as f:
                history = json.load(f)
                for entry in history:
                    self.history_list.insert("end", f"[{entry['timestamp']}] {entry['filename']} -> {entry['category']}\n")
        self.history_list.configure(state="disabled")

    def undo_last_move(self):
        if os.path.exists("history.json"):
            try:
                with open("history.json", 'r') as f:
                    history = json.load(f)
                if history:
                    entry = history[0]
                    if self.sorter.undo_move(entry):
                        history.pop(0)
                        with open("history.json", 'w') as f:
                            json.dump(history, f, indent=4)
                        self.refresh_history()
                        messagebox.showinfo("Undo", f"Recovered: {entry['filename']}")
                    else:
                        messagebox.showerror("Error", "Undo failed. File may have been moved or deleted.")
                else:
                    messagebox.showinfo("Info", "History is empty.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load history: {e}")

    def scan_existing_files(self):
        sources = self.config.get("source_folders", [])
        target = self.config.get("target_folder")
        inplace = self.config.get("inplace_organization", True)
        if sources: threading.Thread(target=self.run_multi_scan, args=(sources, target, inplace), daemon=True).start()

    def run_multi_scan(self, sources, global_target, inplace):
        self.btn_scan.configure(state="disabled", text="Scanning...")
        for source in sources:
            if os.path.exists(source):
                files = [f for f in os.listdir(source) if os.path.isfile(os.path.join(source, f))]
                for filename in files:
                    self.sorter.organize_file(os.path.join(source, filename), source if inplace else global_target)
                    self.after(0, self.refresh_history)
        self.btn_scan.configure(state="normal", text="Run Manual Scan")

    def setup_tray(self):
        image = Image.new('RGB', (64, 64), "black")
        dc = ImageDraw.Draw(image)
        dc.ellipse((16, 16, 48, 48), fill="blue")
        menu = pystray.Menu(pystray.MenuItem("Show", self.show_window), pystray.MenuItem("Exit", self.quit_app))
        self.icon = pystray.Icon("SortAI", image, "SortAI", menu)

    def show_window(self, icon=None, item=None):
        self.icon.stop()
        self.after(0, self.deiconify)

    def quit_app(self, icon=None, item=None):
        self.icon.stop()
        if self.watcher: self.watcher.stop()
        self.quit()
        sys.exit()

if __name__ == "__main__":
    app = SortAIApp()
    app.mainloop()
