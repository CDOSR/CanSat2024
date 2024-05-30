import time, os, sys
import os, time
from converters import timeConverter, fn_timeConverter


def join_paths(*args):
    """Join paths, ensuring correct handling of slashes."""
    # Strip unnecessary slashes and join paths with a single slash
    return '/' + '/'.join(arg.strip('/') for arg in args)

class Logger:
    # This class is used to log the data ect.
   
    def __init__(self, baseDirectory = '/BaseSD',
                workingDirectory = 'CanSat2024Data/',
                daytime = time.time(), 
                init_time = time.ticks_ms(), 
                sleep = 0.001):
        self.baseDirectory = baseDirectory.rstrip('/')
        self.workingDirectory = workingDirectory.strip('/')
        self.init_time = init_time
        self.daytime = daytime
        self.sleep = sleep
        self.environment_setup()
        #self.files_setup(subdir=filename)

    def printout(self, message, file, level, save_log = False):
        """prints the message if verbosity is not lower than <<min_verbosity>>, optionally saves to log"""
        #if min_verbosity >= self.verbosity:
        #    sys.stdout.write(message+"\n")
        if save_log:
            self.logMsg(message, file, level)

    def environment_setup(self):
        # Ensure base directory exists
        self.ensure_directory(self.baseDirectory)

        # Full path for working directory
        full_path = join_paths(self.baseDirectory, self.workingDirectory)
        self.ensure_directory(full_path)
        print(14*" "+'Environment setup complete. Working Directory: {}'.format(full_path))

    def ensure_directory(self, path):
        """Ensure that the specified directory exists, creating it if it does not, including any intermediate directories."""
        parts = path.strip('/').split('/')
        path_to_create = ''
        for part in parts:
            path_to_create += '/' + part
            try:
                os.mkdir(path_to_create)
                # print(14*" "+"Directory created:", path_to_create)
            except OSError as e:
                if e.args[0] == 17:  # errno.EEXIST, directory exists
                    # print(14*" "+"Directory already exists:", path_to_create)
                    continue
                elif e.args[0] == 19:  # errno.ENODEV, no such device
                    # print(14*" "+"No such device:", path_to_create)
                    break  # Stop trying to create directories if the device isn't available
                else:
                    # print(14*" "+"Failed to create directory {}: {}".format(path_to_create, str(e)))
                    break  # Stop further processing on other errors


    def timestamp(self):
        """ Returns time from start in seconds with 3 decimal points """
        #print('{}'.format(time.ticks_ms()- self.init_time))
        return ((time.ticks_ms()-self.init_time) / 1000)

    def presentTime(self):
        """ Returns present time """
        timedelta_ms = (time.monotonic_ns()-self.init_time) % 1000
        present_time = '{0}.{1:03d}'.format(timeConverter(time.localtime()), timedelta_ms)
        return present_time
   

    def logMsg(self, message = '', file = 'log', level = 'info'):
        """ Logs the message to the log """
        if (message != ''):
            # Get the path to the log file
            path = '{}'.format(self.getPath(logName = file))
            #print('  logMsg path: {}'.format(path))
            # with open(path, 'a+') as log:
            #     # Log the message
            #     log.write('[{0:8.3f}]::[{1}]: -{2}- {3} \n'.format(self.timestamp(),
            #                                                 self.presentTime(),
            #                                                 level,
            #                                                 message))
            print(message)

    def getPath(self, logName=''):
        """ Returns the path to a datalog. If the logName argument is None, return the data path """ 
        base_path = self.baseDirectory + '/' + self.workingDirectory.rstrip('/')
        if logName:
            if logName != 'log':
                # Returns the path to a specific log
                path = '{}/{}.txt'.format(base_path, logName)
            else:
                # Return the path to the log file
                path = '{}/{}.txt'.format(base_path, logName)
        else:
            # Returns the path to the data directory
            path = base_path
        return path

    def files_setup(self, subdir=fn_timeConverter(time.localtime())):
        directory = self.baseDirectory + '/' + self.workingDirectory 
        if not directory.endswith('/'):
            directory += '/'
        log_file_name = directory + subdir + ".json"
        return directory, log_file_name

    def saveData(self, category, directory, time1, time2, data = 'None'):
        """ Args: 
            The data:
               (self exsplanitory) 
            Category takes a string, can be ether one of these:
               (acc, temp, pre), care if you use any other categories than these the program will save to a random file
        """
        print('  - {}'.format(data))
        if (type(data) == list or type(data) == tuple):
            # Format the data differently
            newData = ''
            pdata = ''
            for d in data:
                print('    - inside savedata: {}{}'.format(type(d),(d)))
                if (type(d) == float or type(d) == int):
                    newData = (''.join(";{:.6f}".format(d)))
                if (type(d) == list):
                    tmpData = [';' + ("{0}".format(k)) for k in d]
                    newData = ''.join(tmpData)
                if (type(d) == tuple):
                    tmpData = [';' + ("{0}".format(d[k])) for k in range(len(d))]
                    newData = ''.join(tmpData)
                if (type(d) == str):
                    if (d ==''):
                        newData = ''.join(";0")
                    else:
                        newData = ''.join(";"+d)
                for c in set(' []'):
                    newData = newData.replace(c,'')
                newData = newData.replace(',',';')                                  
                pdata +=newData
                print('      - pdata: {0}::{1}'.format(newData, pdata))
        else:
            # Format the data in the regular way
            pdata = ';{0}'.format(str(data))

        path = self.getPath(directory)
        try:
            with open(path, 'a+') as file:
                # Write the time and data to the datalog of the category specified
                if (time1 == '' and time2 == ''):
                    file.write("{0}{1}\n".format(category, pdata))
                else:
                    file.write("{0};{1};{2}{3}\n".format(category, time1, time2, pdata))
        except IOError as e:
            # log the error if there is an error
            self.logMsg(message ='File Not Found... {0}. Error {1}\n'.format(path, e), level = 'error')

    def current_time():
        # Returns the current time in milliseconds since some arbitrary point
        return time.ticks_ms()