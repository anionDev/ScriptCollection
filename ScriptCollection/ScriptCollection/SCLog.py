
from enum import Enum
from datetime import datetime
from .GeneralUtilities import GeneralUtilities


class LogLevel(Enum):
    Quiet = 0
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

    def __init__(self, log_file: str = None, loglevel: LogLevel = None, add_overhead: bool = False):
        self.log_file = log_file
        self.loglevel = loglevel
        self.add_overhead = add_overhead

    @GeneralUtilities.check_arguments
    def log_exception(self, message: str, ex: Exception, current_traceback):
        self.log(f"Exception: {message}; Exception-details: {str(ex)}; Traceback:  {current_traceback.format_exc()}", LogLevel.Error)

    @GeneralUtilities.check_arguments
    def log(self, message: str, loglevel: LogLevel = None):
        for line in GeneralUtilities.string_to_lines(message, True, False):
            self.__log_line(line, loglevel)

    @GeneralUtilities.check_arguments
    def __log_line(self, message: str, loglevel: LogLevel = None):
        if loglevel is None:
            loglevel = LogLevel.Information

        if int(loglevel) > int(self.loglevel):
            return

        part1: str = ""
        part2: str = ""
        part3: str = message

        if loglevel == LogLevel.Warning:
            part3 = f"Warning: {message}"
        if loglevel == LogLevel.Debug:
            part3 = f"Debug: {message}"
        if self.add_overhead:
            part1 = f"[{GeneralUtilities.datetime_to_string_for_logfile_entry(datetime.now())}] ["
            if loglevel == LogLevel.Information:
                part2 = f"Information"
            elif loglevel == LogLevel.Error:
                part2 = f"Error"
            elif loglevel == LogLevel.Warning:
                part2 = f"Warning"
            elif loglevel == LogLevel.Debug:
                part2 = f"Debug"
            else:
                raise ValueError("Unknown loglevel.")
            part3 = f"] {message}"

        print_to_std_out: bool = loglevel in (LogLevel.Debug, LogLevel.Information)
        GeneralUtilities.print_text(part1, print_to_std_out)
        # if the control-characters for colors cause problems then maybe it can be checked with sys.stdout.isatty() if colors should be printed
        if loglevel == LogLevel.Information:
            GeneralUtilities.print_text_in_green(part2, print_to_std_out)
        elif loglevel == LogLevel.Error:
            GeneralUtilities.print_text_in_red(part2, print_to_std_out)
        elif loglevel == LogLevel.Warning:
            GeneralUtilities.print_text_in_yellow(part2, print_to_std_out)
        elif loglevel == LogLevel.Debug:
            GeneralUtilities.print_text_in_cyan(part2, print_to_std_out)
        else:
            raise ValueError("Unknown loglevel.")
        GeneralUtilities.print_text(part3+"\n", print_to_std_out)

        if self.log_file is not None:
            GeneralUtilities.ensure_file_exists(self.log_file)
            GeneralUtilities.append_line_to_file(self.log_file, part1+part2+part3)
