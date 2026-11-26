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

def test_dark_mode_and_tools_dropdown(frontend_url):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.goto(f"{frontend_url}/app.html", wait_until="load")
        modal = page.locator("#onboardingModal")
        if modal.is_visible():
            close_btn = page.locator("#onboardingModal button[onclick*='closeOnboardingModal']")
            if close_btn.count() > 0:
                close_btn.first.click()
            else:
                page.locator("#onboardingModal button").first.click()
            modal.wait_for(state="hidden")
        page.locator("#themeToggle").click()
        assert page.locator("html").get_attribute("data-theme") == "dark"
        page.locator("#toolsMenuBtn").click()
        assert "open" in (page.locator("#toolsDropdown").get_attribute("class") or "")
        page.keyboard.press("Escape")
        assert "open" not in (page.locator("#toolsDropdown").get_attribute("class") or "")
        browser.close()

def test_tyt_score_calculator(frontend_url):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.goto(f"{frontend_url}/app.html", wait_until="load")
        modal = page.locator("#onboardingModal")
        if modal.is_visible():
            close_btn = page.locator("#onboardingModal button[onclick*='closeOnboardingModal']")
            if close_btn.count() > 0:
                close_btn.first.click()
            else:
                page.locator("#onboardingModal button").first.click()
            modal.wait_for(state="hidden")
        page.locator(".tabs .tab-btn").nth(1).click()
        assert page.locator("#tab-1").is_visible()
        page.fill("#tytTr", "30")
        page.fill("#tytMat", "25")
        page.fill("#tytSos", "15")
        page.fill("#tytFen", "10")
        page.fill("#tytObp", "85")
        ham = float(page.locator("#tytHamOut").inner_text().replace(",", "."))
        yer = float(page.locator("#tytYerOut").inner_text().replace(",", "."))
        assert 100.0 <= ham <= 500.0
        assert ham <= yer <= 560.0
        browser.close()


def test_student_invite_hash_mode(frontend_url):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.goto(f"{frontend_url}/app.html#davet=zeynep", wait_until="load")
        assert "active" in (page.locator("#roleOgr").get_attribute("class") or "")
        assert not page.locator("#onboardingModal").is_visible()
        browser.close()


def test_parent_readonly_share_mode(frontend_url):
    import base64
    import json
    payload = {
        "name": "Ali Yilmaz",
        "target": "Tip",
        "goal": 480,
        "tests": [{"date": "2026-11-01", "tyt": 85}],
        "tasks": [{"title": "Matematik", "done": True}],
    }
    encoded = base64.b64encode(json.dumps(payload).encode("utf-8")).decode("ascii")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        errors = []
        page.on("pageerror", lambda err: errors.append(str(err)))
        page.goto(f"{frontend_url}/app.html#veli={encoded}", wait_until="load")
        assert errors == []
        assert not page.locator("#onboardingModal").is_visible()
        assert "Veli Raporu" in page.locator("body").inner_text()
        browser.close()

def test_login_and_register_flow(frontend_url):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()
        page.goto(f"{frontend_url}/login.html#kayit", wait_until="load")
        assert page.locator("#regForm").is_visible()
        page.fill("#regName", "Test Ogrenci")
        page.fill("#regEmail", "test@adimplan.com")
        page.fill("#regPass", "123456")
        page.check("#regKvkk")
        page.locator("#regForm button[type='submit']").click()
        page.wait_for_url("**/app.html")
        assert "app.html" in page.url
        page.goto(f"{frontend_url}/login.html", wait_until="load")
        assert page.locator("#loginForm").is_visible()
        page.fill("#loginEmail", "test@adimplan.com")
        page.fill("#loginPass", "123456")
        page.locator("#loginForm button[type='submit']").click()
        page.wait_for_url("**/app.html")
        assert "app.html" in page.url
        browser.close()
def test_weekly_grid_view_toggle(frontend_url):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 390, "height": 844})
        errors = []
        page.on("pageerror", lambda err: errors.append(str(err)))
        page.goto(f"{frontend_url}/app.html", wait_until="load")
        modal = page.locator("#onboardingModal")
        if modal.is_visible():
            close_btn = page.locator("#onboardingModal button[onclick*='closeOnboardingModal']")
            if close_btn.count() > 0:
                close_btn.first.click()
            else:
                page.locator("#onboardingModal button").first.click()
            modal.wait_for(state="hidden")
        page.locator("#btnViewGrid").click()
        grid = page.locator(".week-grid")
        grid.wait_for(state="visible")
        assert grid.is_visible()
        assert page.locator(".week-grid .week-col").count() == 7
        _assert_no_overflow(page)
        assert errors == []
        browser.close()
        
