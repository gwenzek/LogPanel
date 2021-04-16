import sublime
import logging
import logging.config
import typing
import sys
import io
from types import FrameType
from typing import Optional
from typing import List
from typing import TextIO
from sublime_lib.st3 import sublime_lib
from typing import Dict, TypedDict

CONSOLE_IO: Optional[TextIO] = None


class LoggingSettings(TypedDict):
    version: str
    formatters: Dict[str, dict]
    handlers: Dict[str, dict]
    root: dict
    loggers: Dict[str, dict]


class OutputPanelHandler(logging.StreamHandler):
    @staticmethod
    def create_panel(name: str):
        window = sublime.active_window()
        view = window.find_output_panel(name)
        if not view:
            view = window.create_output_panel(name)
        return sublime_lib.OutputPanel.create(window, name)

    def __init__(self, name: str = "Logging"):
        self.panel = self.create_panel(name)
        super().__init__(self.panel)


class SnitchingStdout:
    def __init__(self, stdout: io.TextIOWrapper):
        self.CONSOLE_IO = stdout
        self._stdout = stdout
        self.logger = logging.getLogger("SublimeLoggingSnitch")
        self.logger.setLevel(0)
        print(f"Stdout will first go through {self} before going to {self._stdout} ({sys.stdout=})", file=self._stdout)
        self.logger.warning(f"Stdout will first go through {self} before going to {self._stdout} ({sys.stdout=})")
        self.buffer: List[str] = []

    def get_line(self, text: str) -> str:
        self.buffer.append(text)
        if not text.endswith("\n"):
            return ""
        line = "".join(self.buffer)
        self.buffer = []
        return line

    def write(self, text):
        # Add options to filter _stdout content
        self._stdout.write(text)

        line = self.get_line(text)
        if not line:
            return
        frame = sys._getframe(1)
        if frame is not None:
            caller = frame.f_code.co_filename
        self.logger.log(1, f"[{caller}] {line.rstrip()}")

    def flush(self):
        self._stdout.flush()

def setup_logging(settings: sublime.Settings = None):
    if settings is None:
        settings = sublime.load_settings("sublime_logging.sublime-settings")
        settings.clear_on_change("loggers")
        settings.add_on_change("loggers", lambda: setup_logging(settings))

    # settings = typing.cast(LoggingSettings, settings.to_dict())
    logger = logging.getLogger("SublimeLogging")
    logger.warning("Logging config will be reseted !")
    logging.config.dictConfig(settings.to_dict())
    logger.warning("Logging has been setup !")


def plugin_loaded():
    setup_logging()

    global CONSOLE_IO
    if CONSOLE_IO is None:
        if isinstance(sys.stdout, sublime._LogWriter):
            CONSOLE_IO = sys.stdout
        else:
            CONSOLE_IO = getattr(sys.stdout, "CONSOLE_IO", None)

    if CONSOLE_IO is None:
        print("Wasn't able to identify Console IO, Snitching is disabled.")
        print(f"{sys.stdout=}, {sys.__stdout__=}")
        print(f"{isinstance(sys.stdout, SnitchingStdout)=}")
        return

    sys.stdout = SnitchingStdout(CONSOLE_IO)
    print("this should be snitched")
