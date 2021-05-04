from pathlib import Path


SETTINGS = "log_panel.sublime-settings"
DEFAULT_SETTINGS = Path(__file__).parent.parent / SETTINGS

def test_read_settings(log_panel):
    settings = """
{
// comment
"version": 1,
// another comment
"loggers": { // trailing comment
// trailing commas
},
}
"""
    assert log_panel._json_parse(settings) == {"version": 1, "loggers": {}}


def test_parse_url_in_comment(log_panel):
    settings = """
    {

    // empty line before comment
    }
    """
    assert log_panel._json_parse(settings) == {}

def test_load_default_settings(log_panel):
    log_panel.read_settings_file(DEFAULT_SETTINGS)
