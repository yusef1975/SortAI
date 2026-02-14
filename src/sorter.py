import os
import shutil
import time
import json
import litellm
from typing import Optional, Dict

class FileSorter:
    def __init__(self, api_key: str = "", openai_key: str = "", anthropic_key: str = "", local_base_url: str = "", model_name: str = "gemini/gemini-2.0-flash", categories: list = None, auto_categories: bool = True):
        self.api_key = api_key
        self.openai_key = openai_key
        self.anthropic_key = anthropic_key
        self.local_base_url = local_base_url
        self.model_name = model_name
        self.categories = categories or []
        self.auto_categories = auto_categories
        self.history_file = "history.json"
        self.ignored_paths = {}  # {path: timestamp}
        
        self._set_env_vars()

    def _set_env_vars(self):
        if self.api_key: os.environ["GEMINI_API_KEY"] = self.api_key
        if self.openai_key: os.environ["OPENAI_API_KEY"] = self.openai_key
        if self.anthropic_key: os.environ["ANTHROPIC_API_KEY"] = self.anthropic_key

    def update_config(self, api_key: str, openai_key: str, anthropic_key: str, local_base_url: str, model_name: str, categories: list, auto_categories: bool):
        self.api_key = api_key
        self.openai_key = openai_key
        self.anthropic_key = anthropic_key
        self.local_base_url = local_base_url
        self.model_name = model_name
        self.categories = categories
        self.auto_categories = auto_categories
        self._set_env_vars()

    def log_history(self, filename, folder, subfolder, destination, original_path):
        entry = {
            "id": str(time.time()),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "filename": filename,
            "category": f"{folder}/{subfolder}",
            "destination": destination,
            "original_path": original_path
        }
        try:
            history = []
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    history = json.load(f)
            history.insert(0, entry)
            history = history[:100]
            with open(self.history_file, 'w') as f:
                json.dump(history, f, indent=4)
        except Exception as e:
            print(f"Error logging history: {e}")

    def undo_move(self, entry):
        """Reverses a move."""
        dest = entry.get("destination")
        orig = entry.get("original_path")
        if dest and orig and os.path.exists(dest):
            try:
                os.makedirs(os.path.dirname(orig), exist_ok=True)
                shutil.move(dest, orig)
                # Add to ignore list to prevent immediate re-sorting
                self.ignored_paths[os.path.abspath(orig)] = time.time()
                return True
            except Exception as e:
                print(f"Undo failed: {e}")
        return False

    def wait_for_file_stability(self, filepath: str, timeout: int = 5):
        """Wait until the file size stops changing."""
        last_size = -1
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                current_size = os.path.getsize(filepath)
                if current_size == last_size and current_size > 0:
                    return True
                last_size = current_size
            except:
                pass
            time.sleep(0.5)
        return False

    def categorize_file(self, filename: str) -> Dict:
        """Uses AI (LiteLLM) to categorize a file based on its name."""
        if not self.api_key:
            return {"folder": "Other", "subfolder": "Misc"}

        prompt = f"""
        Categorize the file '{filename}' into a folder and subfolder.
        Return ONLY a JSON object: {{"folder": "string", "subfolder": "string"}}
        Common folders: Documents, Images, Videos, Music, Code, Archives, etc.
        """
        
        try:
            response = litellm.completion(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                api_base=self.local_base_url if "ollama" in self.model_name.lower() or "localhost" in self.local_base_url else None,
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            print(f"AI Categorization error: {e}")
            return {"folder": "Other", "subfolder": "Misc"}

    def organize_file(self, filepath: str, target_root: str):
        """Moves the file to the organized folder."""
        filepath = os.path.abspath(filepath)
        
        # Check if file was recently undone
        now = time.time()
        if filepath in self.ignored_paths:
            if now - self.ignored_paths[filepath] < 10:  # 10s grace period
                print(f"Skipping {filepath} (recently undone)")
                return False
            else:
                del self.ignored_paths[filepath]

        # Cleanup old ignore entries
        self.ignored_paths = {p: t for p, t in self.ignored_paths.items() if now - t < 10}

        print(f"Processing file: {filepath}")
        if not os.path.exists(filepath):
            return False

        original_path = filepath
        filename = os.path.basename(filepath)
        
        # Skip temporary files
        if filename.endswith(('.tmp', '.crdownload', '.part')):
            return False

        if not self.wait_for_file_stability(filepath):
            return False

        try:
            category = self.categorize_file(filename)
            folder = category.get("folder", "Other")
            subfolder = category.get("subfolder", "Misc")
            
            destination_dir = os.path.join(target_root, folder, subfolder)
            os.makedirs(destination_dir, exist_ok=True)
            
            destination_path = os.path.join(destination_dir, filename)
            
            # Handle duplicates
            if os.path.exists(destination_path):
                base, ext = os.path.splitext(filename)
                counter = 1
                while os.path.exists(destination_path):
                    destination_path = os.path.join(destination_dir, f"{base}_{counter}{ext}")
                    counter += 1
            
            shutil.move(filepath, destination_path)
            print(f"Moved {filename} to {destination_path}")
            self.log_history(filename, folder, subfolder, destination_path, original_path)
            return True
            
        except Exception as e:
            print(f"Failed to organize {filename}: {e}")
            return False
