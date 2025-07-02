from pathlib import Path
import logging
import shutil

import geckodriver_autoinstaller
from selenium import webdriver
from selenium.webdriver.firefox.options import Options


_LOG = logging.getLogger(__name__)

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

    if not shutil.which("firefox"):
        raise RuntimeError("Firefox browser not found. Install it or run with --no-screenshot")

    options = Options()
    options.headless = True
    try:
        driver = webdriver.Firefox(options=options)
    except Exception as exc:
        _LOG.error("Failed to start Firefox: %s", exc)
        raise

    driver.set_window_size(width, height)
    driver.get(url)
    driver.save_screenshot(str(out_path))
    driver.quit()
