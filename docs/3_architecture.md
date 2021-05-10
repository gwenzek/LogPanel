# Architecture

## Core

At its core LogPanel is calling `logging.config.dictConfig` passing the 
content of `log_panel.sublime-settings` file as argument.

Since we need to call `logging.config.dictConfig` in both
the python3.3 and the python3.8 plugin_hosts,
we need to have two instances of the plugin.
For this we copy the `__init__.py` file into a new "LogPanel33" directory.
Since we don't define any commands this copy doesn't create command conflicts.

This also implies that the plugin code must be fully compatible with python3.3.
The 3.3 compatibility is currently not explicitly tested.

## Gotchas

To avoid waiting on `plugin_loaded` we implement our own settings loading.
This helps calling `logging.config.dictConfig` as soon as possible.

Alternatively we could make `LogPanel` a dependency and only plugins that 
do a lot of work at load time would need to add it.

## Logging utils

### OutputPanelHandler

Since one of the goal of the plugin was to allow putting logs into an output
panel, the plugin also contains an "OutputPanelHandler" that implements
the logging.Handler interface and can be used from the dict config file.
The default config already makes use of it to copy all logs into a "Logs" panel,
but more panels can be created.

### AddPyVersion

Adds the Python version to log records, this leverage the `logging.Filter`
interface which despite its name can also be used to add information to log 
records.
The main drawback of this API is that all handlers that want to use the 
`py_version` field must also declare the filter `add_py_version`.

Alternatively we could use `logging.setLogRecordFactory` 
but that can only be done once.

### SnitchingStdout

In order to help plugin authors to migrate to using `logging` instead of `print`
I added an option to mock `sys.stdout`. The mock converts all print calls to a 
`logging.info` calls. The log record is created with `stacklevel=2` to show the
origin of the `print` call.
Since `stacklevel` only exists for Python>=3.8, the snitch doesn't behave the same
way on the two plugin hosts.
If you're interested in having this feature work in both hosts, please let me know.
