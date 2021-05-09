import pytest
import sys
from pathlib import Path

TEST_DIR = Path(__file__).parent


@pytest.fixture(scope="module")
def log_panel():
    """LogPanel codes depend on ST, we can't use it directly in test.

    This fixture creates a "sublime-free" version of LogPanel with only the helpers.
    This allows to keep LogPanel in one file and simplify its loading.
    """
    log_panel_file = str(TEST_DIR.parent / "__init__.py")
    with open(log_panel_file) as f:
        code = f.read().splitlines()
    sections = [(i, l) for i, l in enumerate(code) if l.startswith("###")]

    # Explicit asserts to avoid confusion if we reorganise the file.
    assert sections[0][1] == "### Tools to read .sublime-settings"
    assert sections[1][1] == "### Extra logging tools for users"
    helpers_section = code[: sections[1][0]]
    # Comment sublime import, keep the same line numbers
    helpers_section = [
        "#" + l if l.startswith("import sublime") else l for l in helpers_section
    ]
    # TODO: also load the "Loading helper" section and test it.

    with open(str(TEST_DIR / "log_panel.py"), "w") as o:
        for line in helpers_section:
            print(line, file=o)
    try:
        log_panel = __import__("log_panel")
        log_panel.DEBUG = True
        yield log_panel
    finally:
        (TEST_DIR / "log_panel.py").unlink()
