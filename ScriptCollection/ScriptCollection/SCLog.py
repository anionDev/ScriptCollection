
from enum import Enum
from datetime import datetime,  timezone
from .GeneralUtilities import GeneralUtilities


class LogLevel(Enum):
    Quiet = 0
    Error = 1
    Warning = 2
    Information = 3
    Debug = 4
    Diagnostic = 5

    def __int__(self):
        return self.value


class SCLog:
    loglevel: LogLevel
    log_file: str
    add_overhead: bool
    print_as_color: bool
    zone_of_time: timezone = None

    def __init__(self, log_file: str = None, loglevel: LogLevel = None, add_overhead: bool = False, print_as_color: bool = True):
        self.log_file = log_file
        if loglevel is None:
            self.loglevel = LogLevel.Information
        else:
            self.loglevel = loglevel
        self.add_overhead = add_overhead
        self.print_as_color = print_as_color

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

        if message.endswith("\n"):
            GeneralUtilities.write_message_to_stderr(f"invalid line: '{message}'")  # TODO remove this

        part1: str = GeneralUtilities.empty_string
        part2: str = GeneralUtilities.empty_string
        part3: str = message

        if loglevel == LogLevel.Warning:
            part3 = f"Warning: {message}"
        if loglevel == LogLevel.Debug:
            part3 = f"Debug: {message}"
        if loglevel == LogLevel.Diagnostic:
            part3 = f"Diagnostic: {message}"
        if self.add_overhead:
            moment: datetime = None
            if self.zone_of_time is None:
                moment = datetime.now()
            else:
                moment = datetime.now(self.zone_of_time)
            part1 = f"[{GeneralUtilities.datetime_to_string_for_logfile_entry(moment)}] ["
            if loglevel == LogLevel.Information:
                part2 = f"Information"
            elif loglevel == LogLevel.Error:
                part2 = f"Error"
            elif loglevel == LogLevel.Warning:
                part2 = f"Warning"
            elif loglevel == LogLevel.Debug:
                part2 = f"Debug"
            elif loglevel == LogLevel.Diagnostic:
                part2 = f"Diagnostic"
            else:
                raise ValueError("Unknown loglevel.")
            part3 = f"] {message}"

        print_to_std_out: bool = loglevel in (LogLevel.Debug, LogLevel.Information)
        GeneralUtilities.print_text(part1, print_to_std_out)
        if loglevel == LogLevel.Information:
            GeneralUtilities.print_text_in_green(part2, print_to_std_out, self.print_as_color)
        elif loglevel == LogLevel.Error:
            GeneralUtilities.print_text_in_red(part2, print_to_std_out, self.print_as_color)
        elif loglevel == LogLevel.Warning:
            GeneralUtilities.print_text_in_yellow(part2, print_to_std_out, self.print_as_color)
        elif loglevel == LogLevel.Debug:
            GeneralUtilities.print_text_in_cyan(part2, print_to_std_out, self.print_as_color)
        elif loglevel == LogLevel.Debug:
            GeneralUtilities.print_text_in_cyan(part2, print_to_std_out, self.print_as_color)
        else:
            raise ValueError("Unknown loglevel.")
        GeneralUtilities.print_text(part3+"\n", print_to_std_out)

        if self.log_file is not None:
            GeneralUtilities.ensure_file_exists(self.log_file)
            GeneralUtilities.append_line_to_file(self.log_file, part1+part2+part3)
