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

This package is compatible with both the python3.3 and python3.8 hosts.

## Documentation

* [Get started](docs/1_get_started.md)
* [How to ... ?](docs/2_how_to.md)
* [Overview of this plugin architecture](docs/3_architecture.md)
* [Logging Reference](docs/4_reference.md)

Note this follows the [Diátaxis Framework](https://diataxis.fr/) 
for technical documentation authoring.
I found it interesting as an author and it did helped me write
this documentation.

## Settings and Key bindings

Settings can be found using the command palette "Preferences: Log Panel".

`LogPanel` comes without any command, and therefore any keybinding.
But since it adds two more panels,
I can recommand [SwitchPanel](https://packagecontrol.io/packages/SwitchPanel)
to simplify switching between panels. 
