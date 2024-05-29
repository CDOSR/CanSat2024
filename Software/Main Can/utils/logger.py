import os
import utime
import ujson

class Logger:
    LEVELS = {'DEBUG': 0, 'INFO': 1, 'WARNING': 2, 'ERROR': 3, 'CRITICAL': 4}
    LOG_FILE = 'log.txt'  # Adjust the path according to your system
    MAX_FILE_SIZE = 1024 * 10  # 10KB
    LOG_ROTATION_COUNT = 3  # Keep up to 3 rotated logs
    MIN_CONSOLE_LEVEL = 'ERROR'  # Minimum level to print to console

    def __init__(self, base_directory='/SenderSD', log_directory='CanSat2024Log', log_file=LOG_FILE, level='INFO'):
        self.level = self.LEVELS.get(level, 2)
        self.base_directory = base_directory
        self.log_directory = log_directory
        self.log_path = self.base_directory + '/' + self.log_directory
        self.logfile = log_file
        self.ensure_dir(self.base_directory)
        self.ensure_dir(self.log_path)
        
    def ensure_dir(self, path):
        try:
            # Try to list directory, if it fails, it might not exist
            os.listdir(path)
        except OSError as e:
            # Check if the error is because the directory does not exist
            if e.args[0] == 2:  # ENOENT
                os.mkdir(path)  # Create the directory since it does not exist
            else:
                raise  # Re-raise the exception if it's caused by something else

    def log_event(self, level, message, **kwargs):
        log_entry = {
            'timestamp': utime.time(),
            'localtime' : self.get_timestamp(),
            'level': level,
            'message': message,
            'details': kwargs
        }
        if self.LEVELS[level] >= self.level:
            self.output(log_entry, level)
        # print(str(log_entry).replace("'", '"'))

    def log(self, message, level='INFO'):
        if self.LEVELS[level] >= self.level:
            timestamp = self.get_timestamp()
            log_entry = "[{}] - {} - {}".format(timestamp, level, message)
            self.output(log_entry, level)

    def get_timestamp(self):
        # Returns formatted timestamp
        now = utime.localtime()
        return "{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}".format(
            year=now[0], month=now[1], day=now[2], hour=now[3], minute=now[4], second=now[5])


    def output(self, log_entry, log_level):
        # Check if the log level is above or equal to the minimum console level
        if self.LEVELS[log_level] >= self.LEVELS[self.MIN_CONSOLE_LEVEL]:
            print(log_entry)  # Output to console or serial
        self.write_to_file(log_entry)

    def write_to_file(self, log_entry):
        self.rotate_log()
        filename = self.base_directory + '/' + self.log_directory + '/' + self.logfile
        log_entry_str = ujson.dumps(log_entry)
        try:
            with open(filename, 'a') as file:
                file.write(log_entry_str + '\n')
        except OSError as e:
            print("Failed to write log to file: ", str(e))
            
    def dirname(self, path):
        # Find the last occurrence of '/'
        last_slash_index = path.rfind('/')
        if last_slash_index == -1:
            # No '/' found, so there's no directory part
            return ''
        return path[:last_slash_index]  # Return everything before the last '/'
            
    def ensure_file_exists(self, log_path):
        directory = self.dirname(log_path)
        
#         # Ensure the directory exists
#         if directory and not os.listdir(directory):
#             try:
#                 os.mkdir(directory)
#                 print(f"Created directory: {directory}")
#             except OSError as e:
#                 print(f"Failed to create directory {directory}: {str(e)}")
#                 return  # Exit if the directory cannot be created
        
        # Check if the file exists and create it if it does not
        try:
            with open(log_path, 'a') as file:
                pass  # File exists or has been created
            # print(f"File {log_path} exists or created successfully.")
        except OSError as e:
            print(f"Failed to create file {log_path}: {str(e)}")

    def rotate_log(self):
        log_path = self.base_directory + '/' + self.log_directory + '/' + self.logfile
        self.ensure_file_exists(log_path)
        size = os.stat(log_path)[6]
        try:
            # Check the file size first to decide whether rotation is needed
            if os.stat(log_path)[6] > self.MAX_FILE_SIZE:
                for i in range(self.LOG_ROTATION_COUNT - 1, 0, -1):
                    older_log = "{}.{}.log".format(log_path, i - 1 if i > 1 else '')
                    newer_log = "{}.{}.log".format(log_path, i)
                    if self.ensure_dir(older_log):
                        os.rename(older_log, newer_log)
                os.rename(log_path, log_path + ".0.log")
                open(log_path, 'w').close()  # Create a new log file
        except OSError as e:
            print("Failed to rotate log file: ", str(e))
            self.log("Failed to rotate log file: {}".format(str(e)), "ERROR")
