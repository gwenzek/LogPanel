# SublimeLogging

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

This plugin should be compatible with both the python3.3 and python3.8 hosts.
I'm not sure what's the best way to install both at the same time though.
