# How-To ?

## How to get more detailed logs for a package that you're debugging ?

From the Logs panel, identify the name of the logger used by the package you
want to debug. Open the LogPanel settings from the command palette
"Preferences: LogPanel". From the left side (reference), copy the `"loggers"`
entry to the right. Insert a line like `"MY_PACKAGE": {"level": "DEBUG"},` in
the `loggers` dict. (Where `MY_PACKAGE` is replaced by the name of your
package).


## How to only get the logs of one package into the Log panel

First follow the steps for the previous question, and make sure you have an entry in the "loggers" dict for your plugin. 
From the left side of LogPanel settings, copy the `"root"` entry. 
In the `handlers` list remove the `"log_panel"` entry.
Then add the list `"handlers": ["log_panel"]` to your plugin loggers.
You should have a config like this:

```js
...,
"loggers": {
  "MY_PACKAGE": {"level": "DEBUG" , "handlers": ["log_panel"]},
  ...
},
...
```

## How to make a logging friendly Package

1. use `logging.info` / `logging.warning` / `logging.error` instead of `print`.

2. use `logging.debug` instead of `if debug: print`

2. wrap your commands to catch errors and log them.
Otherwise this will be done by ST itself, bypassing all config set by the users.
`logging.exception(error)` will show the stacktrace of the error.
`log_panel.py` contains `log_errors`,
a function wrapper that can help you do that.

3. if your package does a lot of work at load time,
`LogPanel` may not have been loaded and the logs won't be properly directed.
Since plugins are loaded by alphebetical order and we named this plugin "aaLogPanel" this shouldn't happen often.

