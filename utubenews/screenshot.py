from pathlib import Path
import logging
import shutil

import chromedriver_autoinstaller
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def capture(
    url: str,
    out_path: Path | str,
    *,
    width: int = 1280,
    height: int = 720,
) -> None:
    """Capture the given URL using Chrome/Chromium and save it as a PNG."""
    _LOG = logging.getLogger(__name__)
    # install the appropriate chromedriver for the current platform
    chromedriver_autoinstaller.install()
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    browser = shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")
    if not browser:
        raise RuntimeError("Chrome/Chromium browser not found. Install it or run with --no-screenshot")

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    try:
        driver = webdriver.Chrome(options=options)
    except Exception as exc:
        _LOG.error("Failed to start Chrome: %s", exc)
        raise

    try:
        driver.set_window_size(width, height)
        driver.get(url)

        try:
            # resize window to full page height so the screenshot captures everything
            page_height = driver.execute_script(
                "return document.documentElement.scrollHeight"
            )
            if isinstance(page_height, int) and page_height > height:
                driver.set_window_size(width, page_height)
        except Exception as exc:  # pragma: no cover - best effort
            _LOG.debug("Failed to determine page height: %s", exc)

        driver.save_screenshot(str(out_path))
    finally:
        driver.quit()
