import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading

import pytest
from playwright.sync_api import sync_playwright

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
PAGES = ["index.html", "login.html", "app.html", "admin.html"]
VIEWPORTS = [
    ("desktop", {"width": 1440, "height": 900}),
    ("mobile", {"width": 390, "height": 844}),
]
@pytest.fixture(scope="module")
def frontend_url():
    host = "127.0.0." + "1"
    handler = functools.partial(SimpleHTTPRequestHandler, directory=str(FRONTEND_DIR))
    server = ThreadingHTTPServer((host, 0), handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        server.server_close()


def _assert_no_overflow(page):
    ok = page.evaluate("() => document.documentElement.scrollWidth <= window.innerWidth + 2")
    assert ok, "Horizontal overflow detected"


@pytest.mark.parametrize("vp_name,viewport", VIEWPORTS)
@pytest.mark.parametrize("page_name", PAGES)
def test_pages_load_without_js_errors_or_overflow(frontend_url, vp_name, viewport, page_name):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport=viewport)
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda err: errors.append(str(err)))
        page.goto(f"{frontend_url}/{page_name}", wait_until="load")
        assert errors == [], f"JS errors on {page_name} ({vp_name}): {errors}"
        _assert_no_overflow(page)
        browser.close()


@pytest.mark.parametrize("vp_name,viewport", VIEWPORTS)
def test_app_onboarding_and_all_tabs(frontend_url, vp_name, viewport):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport=viewport)
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda err: errors.append(str(err)))
        page.goto(f"{frontend_url}/app.html", wait_until="load")

        modal = page.locator("#onboardingModal")
        modal.wait_for(state="visible")
        close_btn = page.locator("#onboardingModal button[onclick*='closeOnboardingModal']")
        if close_btn.count() > 0:
            close_btn.first.click()
        else:
            page.locator("#onboardingModal button").first.click()
        modal.wait_for(state="hidden")

        tabs = page.locator(".tabs .tab-btn")
        assert tabs.count() == 6
        for i in range(6):
            tabs.nth(i).click()
            panel = page.locator(f"#tab-{i}")
            assert panel.is_visible(), f"Tab {i} panel not visible on {vp_name}"
            _assert_no_overflow(page)

        assert errors == [], f"JS errors on app.html ({vp_name}): {errors}"
        browser.close()


@pytest.mark.parametrize("vp_name,viewport", VIEWPORTS)
def test_admin_demo_login(frontend_url, vp_name, viewport):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport=viewport)
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda err: errors.append(str(err)))
        page.goto(f"{frontend_url}/admin.html", wait_until="load")

        page.locator("button[onclick*='demoLogin']").click()
        page.locator("#appShell").wait_for(state="visible")
        assert page.locator("#gate").is_hidden()
        _assert_no_overflow(page)

        assert errors == [], f"JS errors on admin.html ({vp_name}): {errors}"
        browser.close()
