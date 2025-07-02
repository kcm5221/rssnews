from pathlib import Path
import tempfile

import geckodriver_autoinstaller
from selenium import webdriver
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.firefox.options import Options


# install the appropriate geckodriver for the current platform
geckodriver_autoinstaller.install()


def capture(
    url: str,
    out_path: Path | str,
    *,
    width: int = 1280,
    height: int = 720,
) -> None:
    """Capture the given URL using Firefox and save it as a PNG."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    temp_profile_dir = tempfile.mkdtemp()
    profile = FirefoxProfile(profile_directory=temp_profile_dir)

    options = Options()
    options.headless = True
    options.profile = profile
    driver = webdriver.Firefox(options=options)
    driver.set_window_size(width, height)
    driver.get(url)
    driver.save_screenshot(str(out_path))
    driver.quit()


