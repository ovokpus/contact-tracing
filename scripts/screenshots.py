"""Capture README screenshots from the running stack (docker compose up). Real UI over the synthetic dataset."""
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parent.parent / "docs" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1400, "height": 1000})
    pg.goto("http://localhost:8080"); pg.wait_for_selector(".pill"); pg.wait_for_load_state("networkidle"); pg.wait_for_timeout(1500)
    pg.screenshot(path=OUT / "01-trace-device.png", full_page=True)
    pg.click("button:text-is('Businesses')"); pg.wait_for_selector("tr.click"); pg.click("tr.click >> nth=0")
    pg.wait_for_selector("th:text-is('Scan time (PT)')"); pg.wait_for_load_state("networkidle"); pg.wait_for_timeout(1500)
    pg.screenshot(path=OUT / "02-business-visitors.png", full_page=True)
    pg.click("button:text-is('Overview')"); pg.wait_for_selector(".bar"); pg.wait_for_timeout(500)
    pg.screenshot(path=OUT / "03-overview.png", full_page=True)
    pg.goto("http://localhost:8000/docs"); pg.wait_for_selector(".opblock")
    pg.screenshot(path=OUT / "04-api-docs.png", full_page=True)
    b.close()
print("ok")
