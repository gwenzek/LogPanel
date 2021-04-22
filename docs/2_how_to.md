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
