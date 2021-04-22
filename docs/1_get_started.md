# Get Started with LogPanel

## Installation

(Not on Package Control yet. Clone this repo in your Package folder)
First install the LogPanel package. 
Using the Sublime Command Palette:  `Package Control: Install Package`. 
Select `LogPanel`.

## Reading the logs

Once the installation is over, right-click in the bottom left corner of the ST
window on the "◧" button. You should see a new entry "Output - Logs".
Select it.

This will open a panel at the bottom of the window containing the logs of all
the ST Packages that uses the standard `logging` module.

You should already see a line like so:
`2021-04-21 23:45:01,663 - LogPanel 3.8 - INFO - Logging for plugin_host 3.8 has been setup !`

This can be split in four parts:
- the time of the log
- the name of the logger (generally the package name),
  followed by the python version used by this package.
- the severity (generally one of DEBUG, INFO, WARNING, ERROR)
- the message

## Writing logs

Now open the ST Console (Right-click on the ◧ button, then "Console"), and write:
`import logging; logging.error("This is bad!")`

Switching back to the "Logs" panel will show the logged message:
`2021-04-21 23:51:03,632 - root 3.8 - ERROR - This is bad !`
