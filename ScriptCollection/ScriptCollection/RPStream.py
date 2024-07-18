import os
import psutil
from .GeneralUtilities import GeneralUtilities
from .ProcessesRunner import ProcessStartInformation, ProcessesRunner
# streams the local libcam-vid-stream to a rtsp-server


class RPStream:

    __working_directory: str = None
    __pid_file: str = None

    def __init__(self, working_directory: str):
        self.__working_directory = working_directory
        self.__pid_file = os.path.join(self.__working_directory, "pid.txt")

    def __get_pid(self) -> str:
        GeneralUtilities.ensure_file_exists(self.__pid_file)
        return GeneralUtilities.read_text_from_file(self.__pid_file)

    def __set_pid(self, pid: str):
        GeneralUtilities.ensure_file_exists(self.__pid_file)
        GeneralUtilities.write_text_to_file(self.__pid_file, pid)

    def __ensure_previous_process_is_not_running(self):
        pid = self.__get_pid()
        if GeneralUtilities.string_has_content(pid):
            for proc in psutil.process_iter():
                if proc.pid == pid and proc.name() == "python":
                    proc.kill()

    def __start_stream(self):
        prinfo: list[ProcessStartInformation] = list[ProcessStartInformation]()
        prinfo.append(ProcessStartInformation(None, "", ""))
        prinfo.append(ProcessStartInformation(None, "", ""))
        processesRunner: ProcessesRunner = ProcessesRunner(prinfo)
        self.__set_pid(str(os.getpid()))
        processesRunner.run()

    def start(self):
        self.__ensure_previous_process_is_not_running()
        self.__start_stream()
