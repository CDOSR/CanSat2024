import json
import os
import time

class DataLogger:
    def __init__(self, base_filename="rcrc24log", max_records=500, max_size=5242880):  # 5 MB limit
        self.base_filename = base_filename
        self.max_records = max_records
        self.max_size = max_size
        self.current_file = None
        self.current_count = 0
        
    def get_file_size(self, filename):
        try:
            return os.stat(filename)[6]
        except OSError:
            return 0
        
    def file_exists(self,filename):
        try:
            os.stat(filename)
            return True
        except OSError:
            return False

    def get_next_filename(self):
        """Generate a filename with a unique timestamp to prevent overwriting."""
        epoch_time = int(time.time())  # Get current epoch time
        filename = f"{self.base_filename}_{epoch_time}.json"
        # The above uses epoch time directly, ensuring uniqueness for each file creation event
        return filename

    def open_new_file(self):
        self.current_file = open(self.get_next_filename(), 'a')
        self.current_count = 0

    def write_data(self, data):
        if not self.current_file or self.current_count >= self.max_records or self.current_file.tell() > self.max_size:
            if self.current_file:
                self.current_file.close()
            self.open_new_file()
        
        self.current_file.write(str(data) + '\n')
        self.current_count += 1

    def close(self):
        if self.current_file:
            self.current_file.close()