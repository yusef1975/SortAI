import json
import os
import sys
from typing import Dict, Any

CONFIG_FILE = "config.json"

DEFAULT_CONFIG: Dict[str, Any] = {
    "openai_api_key": "",
    "anthropic_api_key": "",
    "api_key": "",
    "local_base_url": "http://localhost:11434/v1",
    "active_provider": "gemini",
    "provider": "gemini",
    "model_name": "gemini/gemini-2.0-flash",
    "source_folders": [],  # List of strings
    "target_folder": "",
    "categories": ["School", "Dev Tools", "Books", "Media", "Installers", "Work"],
    "auto_categories": True,
    "auto_start": False,
    "theme": "Dark",
    "inplace_organization": True
}

class ConfigManager:
    def __init__(self, config_file: str = CONFIG_FILE):
        # Resolve path for EXE compatibility
        if getattr(sys, 'frozen', False):
            # Running as a bundled EXE
            base_dir = os.path.dirname(sys.executable)
        else:
            # Running as a script
            base_dir = os.path.dirname(os.path.abspath(__file__))
            # Move up one level if in src/
            if os.path.basename(base_dir) == "src":
                base_dir = os.path.dirname(base_dir)
        
        self.config_file = os.path.join(base_dir, config_file)
        self.config = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        if not os.path.exists(self.config_file):
            return DEFAULT_CONFIG.copy()
        
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return DEFAULT_CONFIG.copy()

    def save_config(self, config: Dict[str, Any]) -> None:
        self.config = config
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)
        except IOError as e:
            print(f"Error saving config: {e}")

    def get(self, key: str) -> Any:
        return self.config.get(key, DEFAULT_CONFIG.get(key))

    def set(self, key: str, value: Any) -> None:
        self.config[key] = value
        self.save_config(self.config)
