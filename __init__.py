import logging
import logging.config
import os
import shutil
import sys

import sublime
import functools
from pathlib import Path

DEBUG = False
logging.raiseExceptions = DEBUG


### Core of the plugin ###

SETTINGS = "log_panel.sublime-settings"


def plugin_loaded():
    settings = sublime.load_settings(SETTINGS)
    pkg_dir = sublime.active_window().extract_variables()["packages"]

    settings.clear_on_change("loggers")
    settings.add_on_change("loggers", lambda: setup_logging(settings, pkg_dir))
    settings.add_on_change("snitch", lambda: setup_snitching(settings))

    setup_logging(settings, pkg_dir)

    if settings.get("snitch", False):
        setup_snitching(settings)


def setup_logging(settings: sublime.Settings, pkg_dir: str):
    logger = logging.getLogger("LogPanel")
    logger.info("Logging config for plugin_host %s will be resetted !", VERSION)
    config = to_dict(settings)
    # Creates directories for logging files.
    for handler in config.get("handlers", {}).values():
        filename = handler.get("filename")
        if not filename:
            continue
        old_filename = filename
        filename = sublime.expand_variables(filename, {"packages": pkg_dir})
        logdir = Path(filename).parent
        _debug("Creating dir for logs:", logdir)
        handler["filename"] = filename
        if logdir.exists():
            continue
        logdir.mkdir(parents=True)

    _debug("config.dictConfig", config["handlers"]["file"])
    logging.config.dictConfig(config)
    logger.info("Logging for plugin_host %s has been setup !", VERSION)
    _debug("LogPanel.getEffectiveLevel() = ", logger.getEffectiveLevel())


def setup_log_panel_33() -> None:
    pkg_dir = Path(__file__).parent.parent.parent / "Packages"
    log_panel_33 = pkg_dir / "LogPanel33"
    log_panel_33.mkdir(exist_ok=True)
    shutil.copyfile(__file__, log_panel_33 / "__init__.py")


# We don't delay this to `plugin_loaded`,
# we want to setup the logging ASAP.
if sys.version_info >= (3, 8):
    setup_log_panel_33()


def to_dict(settings: sublime.Settings) -> dict:
    """Converts the Setting obect into a logging config dict."""
    keys = [
        "version",
        "root",
        "loggers",
        "handlers",
        "formatters",
        "filters",
        "disable_existing_loggers",
    ]
    d = {key: settings.get(key) for key in keys}
    _debug(d)
    return d


### Extra logging tools for users ###


class OutputPanelHandler(logging.Handler):
    """A logging Handler that writes to a ST panel."""

    @staticmethod
    def create_panel(name: str):
        # TODO: This forces the logs to be on the window active at load time.
        # We should add a command to move the panels to another window.
        window = sublime.active_window()
        # Try to append to the existing panel instead of creating a new one.
        view = window.find_output_panel(name)
        if not view:
            view = window.create_output_panel(name)
        return view

    def __init__(self, name: str, level: int = logging.NOTSET):
        super().__init__(level)
        self.name = name
        self.panel = self.create_panel(name)

    def insert_at_end(self, view: sublime.View, message: str) -> None:
        # Move cursor to end so that insertion happens at the end of the ouptut panel.
        selection = view.sel()
        selection.clear()
        selection.add(sublime.Region(view.size()))
        self.panel.run_command("insert", {"characters": message})
        # TODO: restore the original selection

    def emit(self, record: logging.LogRecord) -> None:
        try:
            message = self.format(record) + "\n"
            self.insert_at_end(self.panel, message)
        except Exception:
            if DEBUG:
                logging.raiseExceptions = True
            self.handleError(record)

    def __repr__(self):
        level = logging.getLevelName(self.level)
        return "<%s(%s) (%s)>" % (self.__class__.__name__, self.name, level)


VERSION = "{}.{}".format(*sys.version_info)


class AddPyVersion(logging.Filter):
    """Add the Python version to log records.

    It can be used by formatters using '%(py_version)s'.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        record.py_version = VERSION  # type: ignore
        return True


class SnitchingStdout:
    """Capture `print` calls and log them with their module"""

    def __init__(self, console):
        self.console = console
        self.logger = logging.getLogger("LogPanelSnitch")
        self.logger.info(
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
        # TODO: should this be a log filter instead ?
        frame = sys._getframe(1)
        caller = frame.f_code.co_filename
        if caller == "<string>" or caller.endswith("/logging/__init__.py"):
            # * caller == <string> means printing from the console REPL
            # * don't snitch on logging calls.
            _debug("won't snitch on [{}]".format(caller), file=self.console)
            return n

        # We wan't to show the module / filename of the caller of `write`
        # But stacklevel is new from Python 3.8
        # TODO it's possible to implement this behavior
        # by patching the logger.makeRecord fn:
        # https://stackoverflow.com/questions/49987228/alter-python-logger-stack-level
        if sys.version_info >= (3, 8):
            self.logger.info(message, stacklevel=2)
        else:
            self.logger.info(message)
        return n

    def flush(self):
        self.console.flush()


def setup_snitching(settings: sublime.Settings):
    logger = logging.getLogger("LogPanel")
    console = sys.stdout
    if not isinstance(console, sublime._LogWriter):
        # This happens when hot reloading the package
        console = getattr(sys.stdout, "console", None)
        if console is None or not isinstance(console, sublime._LogWriter):
            logger.error(
                "Wasn't able to identify the Sublime console object, "
                "Snitching is disabled. Try restarting ST."
            )
            logger.error("sys.stdout={}, sys.__stdout={}", sys.stdout, sys.__stdout__)
            return

    if not settings.get("snitch", False):
        # Restore the stdout
        sys.stdout = console
        return
    snitch = SnitchingStdout(console)
    logger.info(
        "Stdout will first go through {} before going to {}",
        snitch,
        snitch.console,
    )
    sys.stdout = snitch
    # TODO: Move this to a test case
    print("This should be snitched to 'Log - Snitch' panel")


def log_errors(logger_name: str):
    """Catch all execptions from the given function and log them.

    It's recommanded to add something similar to your Commands.
    Usage:

    class MyPluginCommand(sublime_plugin.TextCommand):
        @log_errors("MyPlugin")
        def run(self, edit, args):
            ...
    """
    # TODO: Should we try to automatically get a name using the caller module?
    def wrapper(fn):
        @functools.wraps(fn)
        def fn_and_log_errors(*args, **kwargs):
            try:
                fn(*args, **kwargs)
            except Exception as e:
                logging.getLogger(logger_name).exception(e)

        return fn_and_log_errors

    return wrapper


def _debug(*args, **kwargs):
    # Yeah I know, but we need to do print debugging to debug our logging plugin.
    if DEBUG:
        print("[LogPanel-debug]", *args, **kwargs)
