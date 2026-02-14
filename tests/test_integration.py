import unittest
import os
import shutil
import time
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.config import ConfigManager
from src.sorter import FileSorter
from src.watcher import FolderWatcher

# Mock Gemini API for testing without a key
class MockSorter(FileSorter):
    def __init__(self):
        self.model = True # Fake it
        
    def categorize_file(self, filename: str):
        if "invoice" in filename:
            return {"folder": "Work", "subfolder": "Finance"}
        elif "setup" in filename:
            return {"folder": "Installers", "subfolder": "Windows"}
        return {"folder": "Other", "subfolder": "Misc"}
        
    def wait_for_file_stability(self, filepath: str, timeout: int = 1):
        return True

class TestSortAIIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = "test_env"
        self.source = os.path.join(self.test_dir, "source")
        self.target = os.path.join(self.test_dir, "target")
        
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
            
        os.makedirs(self.source)
        os.makedirs(self.target)
        
        self.sorter = MockSorter()
        
    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_sort_logic(self):
        # Create a file
        filename = "invoice_2024.pdf"
        filepath = os.path.join(self.source, filename)
        with open(filepath, 'w') as f:
            f.write("dummy content")
            
        # Run organizer manually
        self.sorter.organize_file(filepath, self.target)
        
        # Check if moved
        expected_path = os.path.join(self.target, "Work", "Finance", filename)
        self.assertTrue(os.path.exists(expected_path))
        self.assertFalse(os.path.exists(filepath))

    def test_watcher_trigger(self):
        # Setup watcher
        watcher = FolderWatcher(self.source, self.target, self.sorter)
        watcher.start()
        
        try:
            # Create file
            filename = "setup_v1.exe"
            filepath = os.path.join(self.source, filename)
            with open(filepath, 'w') as f:
                f.write("exe content")
                
            # Wait for watcher
            time.sleep(2)
            
            # Check if moved
            expected_path = os.path.join(self.target, "Installers", "Windows", filename)
            self.assertTrue(os.path.exists(expected_path))
            
        finally:
            watcher.stop()

if __name__ == '__main__':
    unittest.main()
