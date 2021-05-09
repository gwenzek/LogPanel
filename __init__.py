import io
import json
import logging
import logging.config
import re
import shutil
import sys
from pathlib import Path

import sublime

DEBUG = False
logging.raiseExceptions = DEBUG
logger = logging.getLogger("LogPanel")

### Tools to read .sublime-settings


def _msub(pattern: str, repl: str, string: str) -> str:
    res = re.sub(pattern, repl, string, flags=re.MULTILINE)
    if DEBUG:
        # This is costly, hide it behind a flag
        num_lines = len(string.splitlines())
        res_num_lines = len(res.splitlines())
        assert num_lines == res_num_lines
    return res


def _json_parse(text: str) -> dict:
    og_text = text
    text = _msub(r"^( *)//.*$", "", text)
    text = _msub(r'//[^"\n]*$', "", text)
    text = _msub(r",(\s*)]", r"\1]", text)
    text = _msub(r",(\s*)}", r"\1}", text)

    try:
        return json.loads(text)
    except json.decoder.JSONDecodeError as json_err:
        line, col = json_err.lineno, json_err.colno
        err_lines = text.splitlines()[line - 2 : line]
        err_ctx = "{} {}\n{}: {}\n  {}^".format(
            line - 1, err_lines[0], line, err_lines[1], " " * col
        )
        raise Exception("Invalid json in settings file: \n" + err_ctx) from json_err


def read_settings_file(file: str) -> dict:
    """Read and parse a .sublime-settings file"""
    with open(str(file)) as f:
        text = f.read()
    return _json_parse(text)


def to_dict(settings: dict) -> dict:
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
    return d


### Extra logging tools for users


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
            logging.raiseExceptions = DEBUG
            self.handleError(record)

    def __repr__(self):
        level = logging.getLevelName(self.level)
        return "<%s(%s) (%s)>" % (self.__class__.__name__, self.name, level)


VERSION = "{}.{}".format(*sys.version_info)


class AddPyVersion(logging.Filter):
    """Add the Python version to log records.

    It can be used by formatters using '%(py_version)s'.
    """

    # This could be moved to the log_record_factory, but I'm not sure it's worth it.

    def filter(self, record: logging.LogRecord) -> bool:
        record.py_version = VERSION  # type: ignore
        return True


class SnitchingStdout(io.TextIOWrapper):
    """Capture `print` calls and log them with their module."""

    def __init__(self, console):
        super().__init__(console, encoding="utf8")
        self.console = console
        self.logger = logging.getLogger("LogPanelSnitch")
        self.logger.info(
            "Stdout will first go through %s before going to %s", self, self.console
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


def log_errors(logger_name: str):
    """Catch all execptions from the given function and log them.
    It's recommanded to add something similar to your Commands.
    Usage:
    class MyPluginCommand(sublime_plugin.TextCommand):
        @log_errors("MyPlugin")
        def run(self, edit, args):
            ...
    """
    # TODO: Should we try to automatically get a name using the
    def wrapper(fn):
        @functools.wraps(fn)
        def fn_and_log_errors(*args, **kwargs):
            try:
                fn(*args, **kwargs)
            except Exception as e:
                logging.getLogger(logger_name).exception(e)

        return fn_and_log_errors

    return wrapper


### Logging setup

# Note: this path are only correct when inside
# the ST "Packages" or "Installed Packages" folder.
SETTINGS = "log_panel.sublime-settings"
PKG_DIR = Path(__file__).parent.parent.parent / "Packages"
USER_SETTINGS = str(PKG_DIR / "User" / SETTINGS)
DEFAULT_SETTINGS = str(PKG_DIR / "aaLogPanel" / SETTINGS)


def load_sublime_settings() -> sublime.Settings:
    settings = read_settings_file(DEFAULT_SETTINGS)
    user_settings = read_settings_file(USER_SETTINGS)
    settings.update(user_settings)
    return settings  # type: ignore


def setup_snitching(settings: sublime.Settings):
    console = sys.stdout
    if not isinstance(console, sublime._LogWriter):
        # This happens when hot reloading the package
        console = getattr(sys.stdout, "console", None)
        if console is None or not isinstance(console, sublime._LogWriter):
            logger.error(
                "Wasn't able to identify the Sublime console object, "
                "Snitching is disabled. Try restarting ST."
            )
            logger.error("sys.stdout=%s, sys.__stdout=%s", sys.stdout, sys.__stdout__)
            return

    if not settings.get("snitch", False):
        # Restore the stdout
        sys.stdout = console
        return
    snitch = SnitchingStdout(console)
    logger.info(
        "Stdout will first go through %s before going to %s",
        snitch,
        snitch.console,
    )
    sys.stdout = snitch
    # TODO: Move this to a test case
    print("This should be snitched to 'Log - Snitch' panel")


def setup_logging(settings: sublime.Settings):
    logger.debug("Logging config for plugin_host %s will be resetted !", VERSION)
    config = to_dict(settings)  # type: ignore
    # Creates directories for logging files.
    for handler in config.get("handlers", {}).values():
        filename = handler.get("filename")
        if not filename:
            continue
        logfile = Path(filename)
        if not logfile.is_absolute():
            logfile = PKG_DIR / logfile
        print("Creating dir for logs: %s", logfile)
        handler["filename"] = str(logfile)
        if not logfile.parent.exists():
            logfile.parent.mkdir(parents=True)

    logger.debug("logging.dictConfig = %s", config)
    try:
        logging.config.dictConfig(config)
        logger.info("Logging for plugin_host %s has been setup !", VERSION)
        logger.debug("LogPanel.getEffectiveLevel() = %s", logger.getEffectiveLevel())
        setup_snitching(settings)

    except Exception as e:
        # Catch exception otherwise we can't load the module
        logger.exception(e)


def setup_log_panel_33() -> None:
    log_panel_33 = PKG_DIR / "aaLogPanel33"
    log_panel_33.mkdir(exist_ok=True)

    shutil.copyfile(__file__, log_panel_33 / "__init__.py")


# We don't delay this to `plugin_loaded`,
# we want to setup the logging ASAP.
if sys.version_info >= (3, 8):
    setup_log_panel_33()


setup_logging(load_sublime_settings())


def plugin_loaded():
    """Register triggers to update loading when settings change.

    Note that the logging is not setup here.
    """
    settings = sublime.load_settings(SETTINGS)
    pkg_dir = sublime.active_window().extract_variables()["packages"]

    settings.clear_on_change("loggers")
    settings.add_on_change("loggers", lambda: setup_logging(settings))
