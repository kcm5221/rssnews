import sys
import types
import unittest
from pathlib import Path

def _make_stubs(driver):
    """Insert stub modules for selenium and chromedriver"""
    selenium_mod = types.ModuleType("selenium")
    webdriver_mod = types.ModuleType("selenium.webdriver")
    webdriver_mod.Chrome = lambda *a, **k: driver
    chrome_mod = types.ModuleType("selenium.webdriver.chrome")
    options_mod = types.ModuleType("selenium.webdriver.chrome.options")
    class FakeOptions:
        def add_argument(self, *a, **k):
            pass
    options_mod.Options = FakeOptions
    chrome_mod.options = options_mod
    selenium_mod.webdriver = webdriver_mod

    sys.modules["selenium"] = selenium_mod
    sys.modules["selenium.webdriver"] = webdriver_mod
    sys.modules["selenium.webdriver.chrome"] = chrome_mod
    sys.modules["selenium.webdriver.chrome.options"] = options_mod

    cda_mod = types.ModuleType("chromedriver_autoinstaller")
    cda_mod.install = lambda: None
    sys.modules["chromedriver_autoinstaller"] = cda_mod

class FakeDriver:
    def __init__(self):
        self.quit_called = False
    def set_window_size(self, w, h):
        pass
    def get(self, url):
        raise RuntimeError("boom")
    def execute_script(self, js):
        return 0
    def save_screenshot(self, path):
        pass
    def quit(self):
        self.quit_called = True

class TestCapture(unittest.TestCase):
    def test_quit_on_exception(self):
        driver = FakeDriver()
        # Backup modules possibly replaced
        backups = {name: sys.modules.get(name) for name in [
            "selenium", "selenium.webdriver", "selenium.webdriver.chrome",
            "selenium.webdriver.chrome.options", "chromedriver_autoinstaller",
            "utubenews.screenshot",
        ]}
        try:
            for name in ["utubenews.screenshot"]:
                if name in sys.modules:
                    del sys.modules[name]
            _make_stubs(driver)
            import importlib
            screenshot = importlib.import_module("utubenews.screenshot")
            orig_which = screenshot.shutil.which
            screenshot.shutil.which = lambda *a, **k: "/bin/chrome"
            with self.assertRaises(RuntimeError):
                screenshot.capture("http://x", Path("a.png"))
            self.assertTrue(driver.quit_called)
            screenshot.shutil.which = orig_which
        finally:
            for name, mod in backups.items():
                if mod is not None:
                    sys.modules[name] = mod
                elif name in sys.modules:
                    del sys.modules[name]

if __name__ == "__main__":
    unittest.main()
