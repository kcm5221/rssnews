from pathlib import Path

import geckodriver_autoinstaller
from selenium import webdriver
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

    options = Options()
    options.headless = True
    driver = webdriver.Firefox(options=options)
    driver.set_window_size(width, height)
    driver.get(url)
    driver.save_screenshot(str(out_path))
    driver.quit()
