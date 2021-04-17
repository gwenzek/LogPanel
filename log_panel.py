import logging
import logging.config
import os
import sys

import sublime
from sublime_lib.st3 import sublime_lib

VERSION = "{}{}".format(sys.version_info.major, sys.version_info.minor)
DEBUG = False


def debug(*args, **kwargs):
    # Yeah I know, but we need to do print debugging to debug our logging plugin.
    if DEBUG:
        print("[LogPanel-debug]", *args, **kwargs)


class OutputPanelHandler(logging.StreamHandler):
    @staticmethod
    def create_panel(name: str):
        if VERSION == "33":
            name += " " + VERSION
        window = sublime.active_window()
        # Try to append to the existing panel instead of creating a new one.
        view = window.find_output_panel(name)
        if not view:
            view = window.create_output_panel(name)
        return sublime_lib.OutputPanel.create(window, name)

    def __init__(self, name: str):
        self.panel = self.create_panel(name)
        super().__init__(self.panel)

    def emit(self, record) -> None:
        # Move cursor to end so that insertion happens at the end of the ouptut panel.
        self.panel.seek_end()
        super().emit(record)
        # TODO: restore the original selection


class SnitchingStdout:
    def __init__(self, console):
        self.console = console
        self.logger = logging.getLogger("LogPanelSnitch")
        self.logger.warning(
            "Stdout will first go through {} before going to {}", (self, self.console)
        )
        self._buffer = []

    def get_message(self, text: str) -> str:
        # TODO: this can still insert newlines when not desired.
        self._buffer.append(text)
        if "\n" not in text:
            return ""
        line = "".join(self._buffer)
        self._buffer = []
        return line.rstrip("\n")

    def write(self, text: str) -> int:
        # TODO: Add options to filter console content
        # n = self.console.write(text.replace("\n", " ✓\n"))
        n = self.console.write(text)

        message = self.get_message(text)
        if not message:
            return n
        frame = sys._getframe(1)
        caller = frame.f_code.co_filename
        if caller == "<string>" or caller.endswith("/logging/__init__.py"):
            # * caller == <string> means printing from the console REPL
            # * don't snitch on logging calls.
            debug("won't snitch on [{}]".format(caller), file=self.console)
            return n
        self.logger.info(message)
        return n

    def flush(self):
        self.console.flush()


def to_dict(settings: sublime.Settings) -> dict:
    keys = ["version", "formatters", "handlers", "root", "loggers", "disable_existing_loggers"]
    d = {key: settings.get(key) for key in keys if settings.has(key)}
    debug(d)
    return d


def setup_logging(settings: sublime.Settings):
    logger = logging.getLogger("LogPanel")
    logger.warning("Logging config for plugin_host {} will be resetted !".format(VERSION))
    logging.config.dictConfig(to_dict(settings))
    logger.warning("Logging for plugin_host {} has been setup !".format(VERSION))
    print("Logging for plugin_host {} should have been setup.".format(VERSION))
    debug("LogPanel.getEffectiveLevel() = ", logger.getEffectiveLevel())


def plugin_loaded():
    settings = sublime.load_settings("sublime_logging.sublime-settings")
    settings.clear_on_change("loggers")
    settings.add_on_change("loggers", lambda: setup_logging(settings))

    setup_logging(settings)

    if settings.get("snitch", False):
        setup_snitching()


def setup_snitching():
    logger = logging.getLogger("LogPanel")
    console = sys.stdout
    if not isinstance(console, sublime._LogWriter):
        # This happens when hot reloading the package
        console = getattr(sys.stdout, "console", None)
        if console is None:
            logger.error(
                "Wasn't able to identify the Sublime console object, "
                "Snitching is disabled. Try restarting ST."
            )
            logger.error("sys.stdout={}, sys.__stdout={}", sys.stdout, sys.__stdout__)
            return

    snitch = SnitchingStdout(console)
    logger.info(
        "Stdout will first go through {} before going to {}",
        snitch,
        snitch.console,
    )
    sys.stdout = snitch
    print("this should be snitched to LoggingSnitch panel")
