# LogPanel

Gather all the logging across ST packages into a dedicated panel.

Through the config you can easily:
* lower or raise the overall verbosity of the logs
* silence a particular package
* create dedicated panel for a particular package
* removes the need to have `debug` setting in your package
  - just use `logger.debug` and add a new handler when you want to debug it.
* find packages still using `print` (looking at you PackageControl)
  - enable `"snitch": true` in the config


## Compatibility

This package should be compatible with both the python3.3 and python3.8 hosts.
I'm not sure what's the best way to install both at the same time though.

## Make a logging friendly Package

1. use `logging.info` / `logging.warning` / `logging.error` instead of `print`.

2. use `logging.debug` instead of `if debug: print`

2. wrap your commands to catch errors and log them.
Otherwise this will be done by ST itself, bypassing all config set by the users.
`logging.exception(error)` will show the stacktrace of the error.
`log_panel.py` contains `log_errors`,
a function wrapper that can help you do that.

3. if your package does a lot of work at load time,
`LogPanel` may not have been loaded
and the logs won't be properly directed.
In this case consider making
`LogPanel` a dependency of your package.


## Key bindings

`LogPanel` comes without any command,
and therefore any keybinding.
But since it adds two more panels,
I can recommand [SwitchPanel](https://packagecontrol.io/packages/SwitchPanel)
to simplify switching between panels. 
