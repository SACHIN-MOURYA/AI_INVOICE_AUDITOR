"""
Invoice Monitor Agent - Watches for new invoice files
"""
import os
import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class InvoiceHandler(FileSystemEventHandler):
    def __init__(self, callback):
        self.callback = callback
        
    def on_created(self, event):
        if event.is_directory:
            return
        
        file_path = event.src_path
        if file_path.endswith(('.pdf', '.docx', '.png', '.jpg')):
            # Wait for file to be fully written
            time.sleep(1)
            print(f"New invoice detected: {os.path.basename(file_path)}")
            self.callback(file_path)

class MonitorAgent:
    def __init__(self, watch_path="./data/incoming", callback=None):
        self.watch_path = watch_path
        self.callback = callback or self.default_callback
        
    def default_callback(self, file_path):
        print(f"Processing: {file_path}")
        
    def start(self):
        print(f"Monitoring: {self.watch_path}")
        observer = Observer()
        observer.schedule(InvoiceHandler(self.callback), self.watch_path)
        observer.start()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()


# if __name__ == "__main__":
#     monitor = MonitorAgent()
#     monitor.start()