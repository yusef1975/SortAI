import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from src.sorter import FileSorter
import os

class FileEventHandler(FileSystemEventHandler):
    def __init__(self, sorter: FileSorter, target_folder: str, inplace: bool = False):
        self.sorter = sorter
        self.target_folder = target_folder
        self.inplace = inplace

    def on_created(self, event):
        if not event.is_directory:
            print(f"File created: {event.src_path}")
            # Run in a separate thread or just call directly (watchdog callbacks are in a thread)
            target = os.path.dirname(event.src_path) if self.inplace else self.target_folder
            self.sorter.organize_file(event.src_path, target)

    def on_moved(self, event):
        if not event.is_directory:
            print(f"File moved: {event.dest_path}")
            target = os.path.dirname(event.dest_path) if self.inplace else self.target_folder
            self.sorter.organize_file(event.dest_path, target)

class FolderWatcher:
    def __init__(self, source_folders: list, target_folder: str, sorter: FileSorter, on_move_callback=None, inplace: bool = False):
        self.source_folders = source_folders
        self.target_folder = target_folder
        self.sorter = sorter
        self.inplace = inplace
        self.observer = Observer()
        self.handler = FileEventHandler(sorter, target_folder, inplace)
        self.on_move_callback = on_move_callback

    def wrap_organize(self, filepath):
        target = os.path.dirname(filepath) if self.inplace else self.target_folder
        success = self.sorter.organize_file(filepath, target)
        if success and self.on_move_callback:
            self.on_move_callback()

    def start(self):
        for folder in self.source_folders:
            if os.path.exists(folder):
                self.observer.schedule(self.handler, folder, recursive=False)
                print(f"Started watching {folder} (In-place: {self.inplace})")
        
        if self.observer.emitters:
            self.observer.start()

    def stop(self):
        if self.observer.is_alive():
            self.observer.stop()
            self.observer.join()
        print("Stopped watching folder.")

    def update_folders(self, source_folders: list, target: str, inplace: bool):
        self.stop()
        self.source_folders = source_folders
        self.target_folder = target
        self.inplace = inplace
        self.handler.target_folder = target
        self.handler.inplace = inplace
        self.observer = Observer() # Re-init observer
        self.start()
