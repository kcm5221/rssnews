from pathlib import Path
from typing import Union
from playwright.sync_api import sync_playwright


def capture(
    url: str,
    out_path: Union[str, Path],
    *,
    width: int = 1280,
    height: int = 720,
    full_page: bool = True,
    timeout_ms: int = 60_000,
) -> None:
    """Capture the given URL and save it as a PNG."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": width, "height": height})
        page.goto(url, timeout=timeout_ms)
        page.wait_for_load_state("networkidle")
        page.screenshot(path=str(out_path), full_page=full_page)
        browser.close()

