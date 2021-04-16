import logging
import logging.config
import sys
from typing import Dict, List, Optional, TextIO, TypedDict

import sublime
from sublime_lib.st3 import sublime_lib

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
        # Try to append to the existing panel instead of creating a new one.
        view = window.find_output_panel(name)
        if not view:
            view = window.create_output_panel(name)
        return sublime_lib.OutputPanel.create(window, name, force_writes=False,)

    def __init__(self, name: str):
        self.panel = self.create_panel(name)
        super().__init__(self.panel)


class SnitchingStdout:
    def __init__(self, stdout: TextIO):
        self.CONSOLE_IO = stdout
        self._stdout = stdout
        self.logger = logging.getLogger("SublimeLoggingSnitch")
        self.logger.warning(
            f"Stdout will first go through {self} before going to {self._stdout} ({sys.stdout=})"
        )
        self._buffer: List[str] = []

    def get_line(self, text: str) -> str:
        self._buffer.append(text)
        if "\n" not in text:
            return ""
        line = "".join(self._buffer)
        self._buffer = []
        return line

    def write(self, text: str) -> int:
        # Add options to filter _stdout content
        n = self._stdout.write(text.replace("\n", " ✓\n"))

        line = self.get_line(text)
        if not line:
            return n
        # TODO: try to skip writes from the logging module
        frame = sys._getframe(1)
        if frame is not None:
            caller = frame.f_code.co_filename
        if caller in "<string>":
            return n
        self.logger.info(line)
        return n

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
            # This happens when hot reloading the package
            CONSOLE_IO = getattr(sys.stdout, "CONSOLE_IO", None)

    if CONSOLE_IO is None:
        print("Wasn't able to identify Console IO, Snitching is disabled.")
        print(f"{sys.stdout=}, {sys.__stdout__=}")
        print(f"{isinstance(sys.stdout, SnitchingStdout)=}")
        return

    snitch = SnitchingStdout(CONSOLE_IO)
    print(
        f"Stdout will first go through {snitch} before going to {snitch._stdout}",
        file=snitch._stdout,
    )
    sys.stdout = snitch
    print("this should be snitched")
