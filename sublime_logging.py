import logging
import logging.config
import os
import sys
from typing import Dict, List, Optional, TextIO

import sublime
from sublime_lib.st3 import sublime_lib


class OutputPanelHandler(logging.StreamHandler):
    @staticmethod
    def create_panel(name: str):
        window = sublime.active_window()
        # Try to append to the existing panel instead of creating a new one.
        view = window.find_output_panel(name)
        if not view:
            view = window.create_output_panel(name)
        return sublime_lib.OutputPanel.create(window, name)

    def __init__(self, name: str):
        self.panel = self.create_panel(name)
        super().__init__(self.panel)


class SnitchingStdout:
    def __init__(self, console: TextIO):
        self.console = console
        self.logger = logging.getLogger("SublimeLoggingSnitch")
        self.logger.warning(
            f"Stdout will first go through {self} before going to {self.console}"
        )
        self._buffer: List[str] = []

    def get_line(self, text: str) -> str:
        self._buffer.append(text)
        if os.linesep not in text:
            return ""
        line = "".join(self._buffer)
        self._buffer = []
        return line

    def write(self, text: str) -> int:
        # Add options to filter _console content
        # n = self.console.write(text.replace("\n", " ✓\n"))
        n = self.console.write(text)

        line = self.get_line(text)
        if not line:
            return n
        frame = sys._getframe(1)
        if frame is not None:
            caller = frame.f_code.co_filename
        if caller in "<string>":
            # Called from the console REPL
            # TODO: try to also skip writes from the logging module
            return n
        self.logger.info(line.rstrip(os.linesep))
        return n

    def flush(self):
        self._stdout.flush()


def setup_logging(settings: sublime.Settings = None):
    if settings is None:
        settings = sublime.load_settings("sublime_logging.sublime-settings")
        settings.clear_on_change("loggers")
        settings.add_on_change("loggers", lambda: setup_logging(settings))

    logger = logging.getLogger("SublimeLogging")
    logger.warning("Logging config will be reseted !")
    logging.config.dictConfig(settings.to_dict())
    logger.warning("Logging has been setup !")


def plugin_loaded():
    setup_logging()
    logger = logging.getLogger("SublimeLogging")

    console: Optional[TextIO] = sys.stdout
    if not isinstance(console, sublime._LogWriter):
        # This happens when hot reloading the package
        console = getattr(sys.stdout, "console", None)
        if console is None:
            logger.error(
                "Wasn't able to identify the Sublime console object, "
                "Snitching is disabled. Try restarting ST."
            )
            logger.error(f"{sys.stdout=}, {sys.__stdout__=}")
            return

    snitch = SnitchingStdout(console)
    logger.info(
        f"Stdout will first go through {snitch} before going to {snitch._stdout}",
        file=snitch._stdout,
    )
    sys.stdout = snitch
    print("this should be snitched")
