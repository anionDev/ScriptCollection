
from enum import Enum
from datetime import datetime
from .GeneralUtilities import GeneralUtilities


class LogLevel(Enum):
    Error = 1
    Warning = 2
    Information = 3
    Debug = 4

    def __int__(self):
        return self.value


class SCLog:
    loglevel: LogLevel
    log_file: str
    add_overhead: bool

    def __init__(self, log_file: str = None):
        self.add_overhead = False
        self.loglevel = LogLevel.Information
        self.log_file = log_file

    @GeneralUtilities.check_arguments
    def log_exception(self, message: str, ex: Exception, current_traceback):
        self.log(f"Exception: {message}; Exception-details: {str(ex)}; Traceback:  {current_traceback.format_exc()}", LogLevel.Error)

    @GeneralUtilities.check_arguments
    def log(self, message: str, loglevel: LogLevel):
        if loglevel is None:
            loglevel = LogLevel.Information

        if int(loglevel) > int(self.loglevel):
            return

        if loglevel == LogLevel.Warning:
            message = f"Warning: {message}"
        if self.add_overhead:
            if loglevel == LogLevel.Error:
                message = f"[Error] {message}"
            elif loglevel == LogLevel.Warning:
                message = f"[Warning] {message}"
            elif loglevel == LogLevel.Debug:
                message = f"[Debug] {message}"
            elif loglevel == LogLevel.Information:
                message = f"[Information] {message}"
            else:
                raise ValueError("Unknown loglevel.")

            message = f"[{GeneralUtilities.datetime_to_string_for_logfile_entry(datetime.now())}] {message}"

        if loglevel == LogLevel.Error:
            GeneralUtilities.write_message_to_stderr(message)
        elif loglevel == LogLevel.Warning:
            GeneralUtilities.write_message_to_stderr(message)
        elif loglevel == LogLevel.Debug:
            GeneralUtilities.write_message_to_stdout(message)
        elif loglevel == LogLevel.Information:
            GeneralUtilities.write_message_to_stdout(message)
        else:
            raise ValueError("Unknown loglevel.")

        if self.log_file is not None:
            GeneralUtilities.ensure_file_exists(self.log_file)
            GeneralUtilities.append_line_to_file(self.log_file, message)
