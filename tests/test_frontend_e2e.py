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


SIGNED_IN = "localStorage.setItem('ivme_user', JSON.stringify({name: 'Test Koc', role: 'Bireysel Koç'}));"


def _signed_in_page(browser, **kwargs):
    """A page whose first load already has a signed-in user."""
    context = browser.new_context(**kwargs)
    context.add_init_script(
        "if (!sessionStorage.getItem('_signed')) { sessionStorage.setItem('_signed', '1');" + SIGNED_IN + "}"
    )
    return context.new_page()


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
        page = _signed_in_page(browser, viewport=viewport)
        context = page.context
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


SUPABASE = "https://mkimvsmlxassitajminz.supabase.co"


def _mock_supabase(target, platform_admin=True, owner=True, password="correct-pass"):
    """Fake Supabase Auth/REST so the admin gates can be tested offline."""
    def handle(route):
        request = route.request
        headers = {"access-control-allow-origin": "*", "access-control-allow-headers": "*"}
        if request.method == "OPTIONS":
            return route.fulfill(status=204, headers=headers)
        signed_in = request.headers.get("authorization") == "Bearer good-token"
        status, body = 401, {}
        if "/auth/v1/token" in request.url:
            if request.post_data_json.get("password") == password:
                status, body = 200, {"access_token": "good-token"}
            else:
                status = 400
        elif "/auth/v1/user" in request.url and signed_in:
            status, body = 200, {"id": "u1", "email": "boss@example.com",
                                 "app_metadata": {"platform_admin": platform_admin}}
        elif "/rest/v1/memberships" in request.url and signed_in:
            status, body = 200, ([{"id": "m1"}] if owner else [])
        route.fulfill(status=status, json=body, headers=headers)
    target.route(SUPABASE + "/**", handle)


def _admin_login(page, kind, password="correct-pass"):
    email = "#adminEmailIn" if kind == "admin" else "#em"
    secret = "#adminPassIn" if kind == "admin" else "#pw"
    button = "#adminLoginBtn" if kind == "admin" else "#loginBtn"
    page.fill(email, "boss@example.com")
    page.fill(secret, password)
    page.click(button)


@pytest.mark.parametrize("vp_name,viewport", VIEWPORTS)
def test_admin_owner_login(frontend_url, vp_name, viewport):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport=viewport)
        _mock_supabase(context)
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda err: errors.append(str(err)))
        page.goto(f"{frontend_url}/admin.html", wait_until="load")

        _admin_login(page, "admin")
        page.locator("#appShell").wait_for(state="visible")
        assert page.locator("#gate").is_hidden()
        _assert_no_overflow(page)
        page.reload(wait_until="load")
        page.locator("#appShell").wait_for(state="visible")
        page.evaluate("logoutAdmin()")
        page.reload(wait_until="load")
        assert page.locator("#gate").is_visible()

        assert errors == [], f"JS errors on admin.html ({vp_name}): {errors}"
        browser.close()


@pytest.mark.parametrize("page_name,kind,app", [
    ("admin.html", "admin", "#appShell"), ("super-admin.html", "super", "#app")])
@pytest.mark.parametrize("password,message", [
    ("wrong", "hatalı"), ("correct-pass", "yetkisi yok")])
def test_admin_gates_reject(frontend_url, page_name, kind, app, password, message):
    with sync_playwright() as p:
        with p.chromium.launch() as browser:
            context = browser.new_context()
            _mock_supabase(context, platform_admin=False, owner=False)
            page = context.new_page()
            page.goto(f"{frontend_url}/{page_name}", wait_until="load")
            _admin_login(page, kind, password)
            page.locator("#gateErr").wait_for(state="visible")
            assert message in page.locator("#gateErr").inner_text()
            assert page.locator(app).is_hidden()


@pytest.mark.parametrize("page_name,app", [("admin.html", "#appShell"), ("super-admin.html", "#app")])
def test_admin_gates_ignore_forged_session(frontend_url, page_name, app):
    with sync_playwright() as p:
        with p.chromium.launch() as browser:
            context = browser.new_context()
            _mock_supabase(context)
            context.add_init_script(
                "sessionStorage.setItem('ivme_admin_auth','1');"
                "sessionStorage.setItem('ivme_sa_auth_v1','1');"
                "sessionStorage.setItem('adimplan_auth_owner','forged');"
                "sessionStorage.setItem('adimplan_auth_platform','forged');"
                "localStorage.setItem('ivme_admin_pass','old-secret');")
            page = context.new_page()
            page.goto(f"{frontend_url}/{page_name}", wait_until="networkidle")
            assert page.locator("#gate").is_visible()
            assert page.locator(app).is_hidden()
            assert page.evaluate("localStorage.getItem('ivme_admin_pass')") is None


def test_dark_mode_and_tools_dropdown(frontend_url):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = _signed_in_page(browser, viewport={"width": 1280, "height": 800})
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
        page = _signed_in_page(browser, viewport={"width": 1280, "height": 800})
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
        report = page.locator("#parentView").inner_text()
        assert "Veli Raporu" in report
        assert "Ali Yilmaz" in report and "Matematik" in report and "85" in report
        browser.close()

def test_login_and_register_flow(frontend_url):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()
        # Local-account mode: never let this test reach the real Supabase project.
        context.route("**/config.js", lambda route: route.fulfill(body="", content_type="application/javascript"))
        page.goto(f"{frontend_url}/login.html#kayit", wait_until="load")
        assert page.locator("#registerForm").is_visible()
        page.fill("#regName", "Test Ogrenci")
        page.fill("#regEmail", "test@adimplan.com")
        page.fill("#regPassword", "123456")
        page.check("#regKvkk")
        page.locator("#registerForm button[type='submit']").click()
        page.wait_for_url("**/app.html")
        assert "app.html" in page.url
        page.goto(f"{frontend_url}/login.html", wait_until="load")
        assert page.locator("#loginForm").is_visible()
        page.fill("#loginEmail", "test@adimplan.com")
        page.fill("#loginPassword", "123456")
        page.locator("#loginForm button[type='submit']").click()
        page.wait_for_url("**/app.html")
        assert "app.html" in page.url
        browser.close()
def test_weekly_grid_view_toggle(frontend_url):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = _signed_in_page(browser, viewport={"width": 390, "height": 844})
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
        page.locator(".tabs .tab-btn").first.click()
        page.locator("#btnViewGrid").click()
        grid = page.locator(".week-grid")
        grid.wait_for(state="visible")
        assert grid.is_visible()
        assert page.locator(".week-grid .week-col").count() == 7
        _assert_no_overflow(page)
        assert errors == []
        browser.close()
      
def test_super_admin_desktop_and_mobile(frontend_url):
    with sync_playwright() as p:
        with p.chromium.launch() as browser:
            for vp_name, viewport in VIEWPORTS:
                context = browser.new_context(viewport=viewport)
                _mock_supabase(context)
                page = context.new_page()
                errors = []
                page.on("pageerror", lambda err: errors.append(str(err)))
                page.goto(f"{frontend_url}/super-admin.html", wait_until="load")
                assert errors == [], f"JS errors on super-admin ({vp_name}): {errors}"
                _assert_no_overflow(page)
                _admin_login(page, "super")
                page.locator("#app").wait_for(state="visible")
                assert page.locator("#tab-subs").is_visible()
                _assert_no_overflow(page)
                page.locator(".nav-btn", has_text="CMS").click()
                page.locator("#tab-cms").wait_for(state="visible")
                assert page.locator("#tab-cms").is_visible()
                _assert_no_overflow(page)
                page.locator(".nav-btn", has_text="Abonelikler").click()
                page.locator("#tab-subs").wait_for(state="visible")
                assert page.locator("#tab-subs").is_visible()
                assert errors == [], f"JS errors after tab switch ({vp_name}): {errors}"
                context.close()

def test_super_admin_cms_updates_landing(frontend_url):
    with sync_playwright() as p:
        with p.chromium.launch() as browser:
            context = browser.new_context(viewport={"width": 1440, "height": 900})
            _mock_supabase(context)
            page = context.new_page()
            errors = []
            page.on("pageerror", lambda err: errors.append(str(err)))
            page.goto(f"{frontend_url}/super-admin.html", wait_until="load")
            _admin_login(page, "super")
            page.locator("#app").wait_for(state="visible")
            page.locator(".nav-btn", has_text="CMS").click()
            page.locator("#tab-cms").wait_for(state="visible")
            custom_title = "E2E Ozel Hero Basligi 2026"
            page.fill("#c-heroTitle", custom_title)
            page.locator("#cmsForm button[type='submit']").click()
            page.goto(f"{frontend_url}/index.html", wait_until="load")
            assert custom_title in page.locator("h1").inner_text()
            assert errors == [], f"JS errors on CMS landing update: {errors}"
            context.close()


def _open(browser, url, init_script=""):
    """New page with onboarding skipped, external requests blocked and errors collected."""
    context = browser.new_context(viewport={"width": 1280, "height": 900})
    context.route(lambda u: not u.startswith("http://127.0.0.1"), lambda route: route.abort())
    context.add_init_script(
        "if (!sessionStorage.getItem('_init')) { sessionStorage.setItem('_init', '1');"
        "localStorage.setItem('ivme_onboarding_done', '1');" + SIGNED_IN + init_script + "}"
    )
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda err: errors.append(str(err)))
    page.on("dialog", lambda dialog: dialog.accept())
    page.goto(url, wait_until="load")
    return page, errors


def test_all_inline_handlers_exist(frontend_url):
    """Every function named in an inline on* attribute must be defined."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for name in PAGES + ["super-admin.html"]:
            page, _ = _open(browser, f"{frontend_url}/{name}")
            missing = page.evaluate(
                r"""() => {
                    const names = new Set();
                    document.querySelectorAll('*').forEach(el => [...el.attributes]
                        .filter(a => a.name.startsWith('on'))
                        .forEach(a => {
                            const m = a.value.trim().match(/^([A-Za-z_$][\w$]*)\s*\(/);
                            if (m && !['if', 'return'].includes(m[1])) names.add(m[1]);
                        }));
                    return [...names].filter(n => typeof window[n] !== 'function');
                }"""
            )
            assert missing == [], f"{name}: {missing}"
            page.context.close()
        browser.close()


def test_coach_module_does_not_blank_main_tabs(frontend_url):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page, errors = _open(browser, f"{frontend_url}/app.html")
        page.click("[data-im=students]")
        page.click(".im-nb[data-tab='0']")
        assert page.locator("#tab-0").is_visible()
        page.click(".sidebar-nav-item[data-tab='home']")
        assert page.locator("#tab-home").is_visible()
        assert errors == []
        browser.close()


def test_user_text_is_not_executed_as_html(frontend_url):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page, errors = _open(browser, f"{frontend_url}/app.html")
        page.evaluate(
            """() => {
                window.__xss = 0;
                const evil = '<img src=x onerror="window.__xss=1">';
                cur().name = evil;
                cur().tasks.push({id: 999, title: evil, day: 'Pzt', meta: evil, done: false});
                save(); renderAll(); switchTab(0); toggleSidebarBell();
            }"""
        )
        page.wait_for_timeout(300)
        assert page.evaluate("window.__xss") == 0
        assert errors == []
        browser.close()


def test_curriculum_and_weekly_drag_and_drop(frontend_url):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page, errors = _open(browser, f"{frontend_url}/app.html")
        page.evaluate("switchTab(1)")
        assert "undefined" not in page.locator("#curriculumList").inner_text()
        assert page.locator("#curriculumList select").count() > 0
        page.evaluate("switchTab(0); setProgramView('grid')")
        assert page.evaluate("cur().tasks[0].day") == "Pzt"
        page.drag_and_drop(".week-col[data-day=Pzt] .week-task >> nth=0", ".week-col[data-day=Cum]")
        assert page.evaluate("cur().tasks[0].day") == "Cum"
        assert errors == []
        browser.close()


def test_app_survives_partial_saved_state(frontend_url):
    broken = "localStorage.setItem('adimplan_v2_state', JSON.stringify({students: [], corp: {}}));"
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page, errors = _open(browser, f"{frontend_url}/app.html", broken)
        assert page.locator("#studentSelect option").count() > 0
        assert errors == []
        browser.close()


def test_backup_excludes_secrets(frontend_url):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page, _ = _open(browser, f"{frontend_url}/app.html")
        page.evaluate(
            "localStorage.setItem('ivme_admin_pass', 'SECRET-PASS');"
            "localStorage.setItem('ivme_supabase_anon_key', 'SECRET-KEY')"
        )
        with page.expect_download() as download:
            page.evaluate("exportBackup()")
        content = Path(download.value.path()).read_text(encoding="utf-8")
        assert "SECRET-PASS" not in content and "SECRET-KEY" not in content
        browser.close()


def test_parent_email_request_carries_session_token(frontend_url):
    setup = (
        "localStorage.setItem('ivme_api_url', 'http://127.0.0.1:9');"
        "localStorage.setItem('ivme_supabase_url', 'https://example.supabase.co');"
        "localStorage.setItem('ivme_supabase_anon_key', 'anon');"
        "window.supabase = {createClient: () => ({auth: {getSession: async () =>"
        " ({data: {session: {access_token: 'session-token'}}})}})};"
    )
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page, errors = _open(browser, f"{frontend_url}/app.html", setup)
        page.evaluate(
            """async () => {
                window.__sent = null;
                window.fetch = async (url, options) => {
                    window.__sent = options.headers;
                    return new Response(JSON.stringify({status: 'dry_run'}), {status: 200});
                };
                document.getElementById('parentReport').value = 'Rapor';
                document.getElementById('parentEmailInput').value = 'veli@example.com';
                await sendParentEmail();
            }"""
        )
        assert page.evaluate("window.__sent.Authorization") == "Bearer session-token"
        assert errors == []
        browser.close()


def test_logout_removes_supabase_session(frontend_url):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page, _ = _open(
            browser, f"{frontend_url}/app.html",
            "localStorage.setItem('sb-example-auth-token', 'x');",
        )
        page.evaluate("logoutSession()")
        page.wait_for_url("**/login.html")
        assert page.evaluate("localStorage.getItem('sb-example-auth-token')") is None
        browser.close()


def test_onboarding_does_not_block_returning_user(frontend_url):
    """No forced hiding here: a stray CSS brace once kept this window over the whole app."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page, errors = _open(browser, f"{frontend_url}/app.html")
        assert not page.locator("#onboardingModal").is_visible()
        page.click(".sidebar-nav-item[data-tab='home']", timeout=3000)
        page.evaluate("openOnboardingModal()")
        assert page.locator("#onboardingModal").is_visible()
        assert errors == []
        browser.close()


def test_student_detail_opens_every_tab(frontend_url):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page, errors = _open(browser, f"{frontend_url}/app.html")
        page.click("[data-im=students]")
        page.locator("[data-go^='student_detail:']").first.click()
        tabs = page.eval_on_selector_all("[data-sdt]", "els => els.map(e => e.dataset.sdt)")
        assert len(tabs) >= 9
        for tab in tabs:
            page.click(f"[data-sdt='{tab}']")
            assert page.locator(f"[data-sdt='{tab}'].on").count() == 1
        assert errors == []
        browser.close()


def test_coach_profile_keeps_no_password_and_can_log_out(frontend_url):
    old = (
        "localStorage.setItem('ivme_coach_modules_v1', JSON.stringify("
        "{coach: {name: 'K', email: 'k@example.com', pass: 'plain-secret'}}));"
    )
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page, errors = _open(browser, f"{frontend_url}/app.html", old)
        assert "plain-secret" not in page.evaluate("localStorage.getItem('ivme_coach_modules_v1')")
        page.click("[data-im=profile]")
        assert page.locator("#ivme-mod-host input[type=password]").count() == 0
        page.click("#im-logout-btn")
        page.wait_for_url("**/login.html")
        assert errors == []
        browser.close()


def test_app_requires_login_and_demo_still_works(frontend_url):
    with sync_playwright() as p:
        with p.chromium.launch() as browser:
            page = browser.new_page()
            page.goto(f"{frontend_url}/app.html")
            page.wait_for_url("**/login.html")
            page.click("#demoBtn")
            page.wait_for_url("**/app.html")
            page.wait_for_load_state("load")
            assert page.locator("#sessionLockOverlay").is_hidden()


def test_idle_session_locks_and_reload_does_not_bypass(frontend_url):
    with sync_playwright() as p:
        with p.chromium.launch() as browser:
            page, errors = _open(browser, f"{frontend_url}/app.html")
            page.evaluate("localStorage.setItem('ivme_last_active', String(Date.now() - 31 * 60 * 1000))")
            page.mouse.move(50, 50)
            page.locator("#sessionLockOverlay").wait_for(state="visible")
            assert page.evaluate("localStorage.getItem('ivme_user')") is None
            page.reload()
            page.wait_for_url("**/login.html")
            assert errors == []


def test_stale_session_is_rejected_on_load(frontend_url):
    with sync_playwright() as p:
        with p.chromium.launch() as browser:
            context = browser.new_context()
            context.add_init_script(
                "if (!sessionStorage.getItem('_i')) { sessionStorage.setItem('_i', '1');" + SIGNED_IN +
                "localStorage.setItem('ivme_last_active', '1000');}")
            page = context.new_page()
            page.goto(f"{frontend_url}/app.html")
            page.wait_for_url("**/login.html")


def test_invite_hash_cannot_skip_login_where_coach_data_exists(frontend_url):
    with sync_playwright() as p:
        with p.chromium.launch() as browser:
            page, _ = _open(browser, f"{frontend_url}/app.html")
            assert page.evaluate("localStorage.getItem('adimplan_v2_state') !== null || (save(), true)")
            page.evaluate("logoutSession()")
            page.wait_for_url("**/login.html")
            page.goto(f"{frontend_url}/app.html#davet=zeynep")
            page.wait_for_url("**/login.html")


def test_fresh_invite_survives_reload_but_needs_the_link(frontend_url):
    with sync_playwright() as p:
        with p.chromium.launch() as browser:
            page = browser.new_page()
            page.goto(f"{frontend_url}/app.html#davet=zeynep")
            page.reload()
            assert "app.html#davet" in page.url
            page.goto(f"{frontend_url}/login.html")
            page.goto(f"{frontend_url}/app.html")
            page.wait_for_url("**/login.html")


def test_blocked_visit_does_not_break_a_later_invite(frontend_url):
    with sync_playwright() as p:
        with p.chromium.launch() as browser:
            page = browser.new_page()
            page.goto(f"{frontend_url}/app.html")
            page.wait_for_url("**/login.html")
            page.goto(f"{frontend_url}/app.html#davet=zeynep")
            page.wait_for_load_state("load")
            assert "app.html#davet" in page.url

def test_new_v16_pages_load_without_errors(frontend_url):
    pages = ["program.html", "student.html", "coach-panel.html", "pricing.html"]
    with sync_playwright() as p:
        with p.chromium.launch() as browser:
            for page_name in pages:
                context = browser.new_context()
                context.add_init_script(SIGNED_IN)
                page = context.new_page()
                errors = []
                page.on("pageerror", lambda err, errs=errors: errs.append(str(err)))
                resp = page.goto(f"{frontend_url}/{page_name}", wait_until="load")
                assert resp is not None and resp.status == 200
                assert page.inner_text("body").strip() != ""
                assert errors == []
                context.close()


def test_demo_session_cannot_see_or_change_real_data(frontend_url):
    import json
    with sync_playwright() as p:
        with p.chromium.launch() as browser:
            page, errors = _open(browser, f"{frontend_url}/app.html")
            page.evaluate("state.students[0].name = 'GERCEK-OGRENCI'; save();"
                          "localStorage.setItem('ivme_workspace_key', 'REAL-WORKSPACE-KEY');"
                          "localStorage.setItem('supabase_anon_key', 'REAL-SUPA-KEY')")
            real = page.evaluate("localStorage.getItem('adimplan_v2_state')")
            assert "GERCEK-OGRENCI" in real
            page.evaluate("logoutSession()")
            page.wait_for_url("**/login.html")
            page.click("#demoBtn")
            page.wait_for_url("**/app.html")
            page.wait_for_load_state("load")
            assert "GERCEK-OGRENCI" not in page.content()
            assert page.evaluate("localStorage.getItem('ivme_workspace_key')") is None
            assert page.evaluate("localStorage.getItem('supabase_anon_key')") is None
            page.evaluate("state.students[0].name = 'DEMO-DEGISIKLIK'; save()")
            with page.expect_download() as info:
                page.evaluate("exportBackup()")
            backup = json.dumps(json.load(open(info.value.path(), encoding="utf-8")))
            assert "DEMO-DEGISIKLIK" in backup and "GERCEK-OGRENCI" not in backup
            page.evaluate("logoutSession()")
            page.wait_for_url("**/login.html")
            assert page.evaluate("localStorage.getItem('adimplan_v2_state')") == real
            assert page.evaluate("localStorage.getItem('ivme_workspace_key')") == "REAL-WORKSPACE-KEY"
            assert errors == []


def test_real_backup_still_exports_real_data(frontend_url):
    with sync_playwright() as p:
        with p.chromium.launch() as browser:
            page, _ = _open(browser, f"{frontend_url}/app.html")
            page.evaluate("state.students[0].name = 'GERCEK-OGRENCI'; save()")
            with page.expect_download() as info:
                page.evaluate("exportBackup()")
            assert "GERCEK-OGRENCI" in open(info.value.path(), encoding="utf-8").read()


def test_login_uses_configured_supabase_project(frontend_url):
    stub = """
    window.supabase = { createClient: function (url, key) {
      sessionStorage.setItem('_client', JSON.stringify([url, key]));
      return { auth: { signInWithPassword: async function () {
        return { data: { user: { user_metadata: { role: 'Koç' } } }, error: null };
      } } };
    } };
    """
    with sync_playwright() as p:
        with p.chromium.launch() as browser:
            context = browser.new_context()
            context.route(lambda u: not u.startswith("http://127.0.0.1"), lambda route: route.abort())
            context.route("**/@supabase/supabase-js@2",
                          lambda route: route.fulfill(body=stub, content_type="application/javascript"))
            page = context.new_page()
            page.goto(f"{frontend_url}/login.html")
            page.fill("#loginEmail", "koc@example.com")
            page.fill("#loginPassword", "123456")
            page.locator("#loginForm button[type='submit']").click()
            page.wait_for_url("**/app.html")
            page.wait_for_load_state("load")
            client = page.evaluate("JSON.parse(sessionStorage.getItem('_client'))")
            assert client[0] == "https://mkimvsmlxassitajminz.supabase.co"
            assert client[1].startswith("sb_publishable_")
            assert page.evaluate("getSupaCfg().url") == client[0]
            assert page.input_value("#supaKeyInput") == client[1]


def test_program_page_shows_typed_html_as_text(frontend_url):
    payload = '<img src=x onerror="window.__xss=1">'
    with sync_playwright() as p:
        with p.chromium.launch() as browser:
            context = browser.new_context()
            context.route(lambda u: not u.startswith("http://127.0.0.1"), lambda route: route.abort())
            context.add_init_script("window.tailwind = {};" + SIGNED_IN)
            page = context.new_page()
            page.goto(f"{frontend_url}/program.html")
            page.evaluate("openTaskModal(null, null)")
            page.evaluate("([a]) => { document.getElementById('task-topic').value = a;"
                          " document.getElementById('task-target').value = a; }", [payload])
            before = page.evaluate("state.tasks.length")
            page.evaluate("saveTaskFromModal()")
            page.wait_for_timeout(500)
            assert page.evaluate("state.tasks.length") > before
            assert page.evaluate("window.__xss || 0") == 0
            assert payload in page.locator("body").inner_text()


PANELS = [("student.html", "adimplan_student_state_v1"),
          ("coach-panel.html", "adimplan_coach_panel_v1"),
          ("program.html", "adimplan_program_v1")]


def _offline_context(browser):
    context = browser.new_context()
    context.route(lambda u: not u.startswith("http://127.0.0.1"), lambda route: route.abort())
    context.add_init_script("window.tailwind = {};")
    return context


@pytest.mark.parametrize("name,key", PANELS)
def test_panel_requires_login_then_returns(frontend_url, name, key):
    with sync_playwright() as p:
        with p.chromium.launch() as browser:
            page = _offline_context(browser).new_page()
            page.goto(f"{frontend_url}/{name}")
            page.wait_for_url("**/login.html")
            page.click("#demoBtn")
            page.wait_for_url(f"**/{name}")


@pytest.mark.parametrize("name,key", PANELS)
def test_panel_demo_data_is_separate(frontend_url, name, key):
    with sync_playwright() as p:
        with p.chromium.launch() as browser:
            page = _offline_context(browser).new_page()
            page.goto(f"{frontend_url}/login.html")
            page.evaluate("([k]) => localStorage.setItem(k, 'REAL-DATA')", [key])
            page.evaluate("sessionStorage.setItem('adimplan_next', 'https://evil.example/x')")
            page.click("#demoBtn")
            page.wait_for_url("**/app.html")
            page.goto(f"{frontend_url}/{name}")
            page.wait_for_load_state("load")
            assert page.evaluate("([k]) => localStorage.getItem(k)", [key]) != "REAL-DATA"
            page.evaluate("([k]) => localStorage.setItem(k, 'DEMO-WRITE')", [key])
            page.goto(f"{frontend_url}/login.html")
            assert page.evaluate("([k]) => localStorage.getItem(k)", [key]) == "REAL-DATA"


@pytest.mark.parametrize("name,key", PANELS)
def test_panel_idle_session_ends(frontend_url, name, key):
    with sync_playwright() as p:
        with p.chromium.launch() as browser:
            page = _offline_context(browser).new_page()
            page.goto(f"{frontend_url}/login.html")
            page.click("#demoBtn")
            page.wait_for_url("**/app.html")
            page.goto(f"{frontend_url}/{name}")
            page.evaluate("localStorage.setItem('ivme_last_active', String(Date.now() - 31 * 60 * 1000))")
            page.mouse.move(40, 40)
            page.wait_for_url("**/login.html")
            assert page.evaluate("localStorage.getItem('ivme_user')") is None

def test_auth_callback_index_pkce_redirects_to_login(frontend_url):
    with sync_playwright() as p:
        with p.chromium.launch() as browser:
            page = _offline_context(browser).new_page()
            page_errors = []
            page.on("pageerror", lambda exc: page_errors.append(str(exc)))
            page.goto(f"{frontend_url}/index.html?code=test-pkce-123")
            page.wait_for_url("**/login.html?code=test-pkce-123")
            assert "login.html?code=test-pkce-123" in page.url
            assert page_errors == []


def test_auth_callback_login_error_banner_visible(frontend_url):
    with sync_playwright() as p:
        with p.chromium.launch() as browser:
            page = _offline_context(browser).new_page()
            page_errors = []
            page.on("pageerror", lambda exc: page_errors.append(str(exc)))
            page.goto(
                f"{frontend_url}/login.html?error=access_denied"
                "&error_description=Email+link+is+invalid+or+has+expired"
            )
            page.wait_for_load_state("domcontentloaded")
            alert = page.locator("#authAlert, #adimplanAuthNotice").first
            alert.wait_for(state="visible", timeout=5000)
            assert alert.is_visible()
            assert alert.inner_text().strip() != ""
            assert page_errors == []
            

def test_parent_report_renders_url_params(frontend_url):
    with sync_playwright() as p:
        with p.chromium.launch() as browser:
            page = _offline_context(browser).new_page()
            page_errors = []
            page.on("pageerror", lambda exc: page_errors.append(str(exc)))
            resp = page.goto(
                f"{frontend_url}/parent-report.html?student=Zeynep+Kaya&done=9&total=10&pomodoro=320&net=84.5",
                wait_until="domcontentloaded",
            )
            assert resp is not None and resp.status == 200
            assert page.locator("#reportStudent").is_visible()
            assert page.locator("#reportStudent").inner_text() == "Zeynep Kaya"
            assert page.locator("#kpiCompletion").is_visible()
            assert "%90" in page.locator("#kpiCompletion").inner_text()
            assert page_errors == []


def test_optical_reader_loads_and_scores(frontend_url):
    with sync_playwright() as p:
        with p.chromium.launch() as browser:
            page = _offline_context(browser).new_page()
            page_errors = []
            page.on("pageerror", lambda exc: page_errors.append(str(exc)))
            resp = page.goto(
                f"{frontend_url}/optical-reader.html",
                wait_until="domcontentloaded",
            )
            assert resp is not None and resp.status == 200
            table = page.locator("#resultsTable")
            table.wait_for(state="visible", timeout=5000)
            assert table.is_visible()
            rows = page.locator("#resultsBody tr")
            assert rows.count() >= 3
            assert "Ahmet Yılmaz" in page.locator("#resultsBody").inner_text()
            assert page_errors == []



@pytest.mark.parametrize("google_enabled", [True, False])
def test_google_button_follows_supabase_provider_setting(frontend_url, google_enabled):
    stub = (
        "window.supabase = {createClient: () => ({auth: {"
        "onAuthStateChange: () => {},"
        "signInWithOAuth: async (o) => { window.__oauth = o; return {}; }}})};"
    )
    with sync_playwright() as p:
        with p.chromium.launch() as browser:
            page = browser.new_context(service_workers="block").new_page()
            page.route("**/cdn.jsdelivr.net/**", lambda r: r.fulfill(body=stub, content_type="application/javascript"))
            page.route(
                "**/auth/v1/settings",
                lambda r: r.fulfill(
                    json={"external": {"google": google_enabled}},
                    headers={"access-control-allow-origin": "*", "access-control-allow-headers": "*"},
                ),
            )
            with page.expect_response("**/auth/v1/settings"):
                page.goto(f"{frontend_url}/login.html")
            button = page.locator("#googleBtn")
            if not google_enabled:
                page.wait_for_timeout(300)
                assert not button.is_visible()
                return
            button.click()
            options = page.evaluate("window.__oauth")
            assert options["provider"] == "google"
            assert options["options"]["redirectTo"] == f"{frontend_url}/login.html"


def test_student_sections_are_inside_main_and_toolbar_collapses(frontend_url):
    with sync_playwright() as p:
        with p.chromium.launch() as browser:
            context = _offline_context(browser)
            context.add_init_script(SIGNED_IN)
            page = context.new_page()
            page.goto(f"{frontend_url}/student.html")
            assert page.locator("section.section-view").count() > 0
            assert page.locator("main section.section-view").count() == page.locator("section.section-view").count()
            toggle = page.locator("#adimplan-student-live-toggle")
            pomodoro = page.get_by_text("+25 dk Pomodoro Kaydet")
            toggle.click()
            assert not pomodoro.is_visible()
            toggle.click()
            assert pomodoro.is_visible()


@pytest.mark.parametrize(
    "code,message,expected",
    [
        ("invalid_credentials", "Invalid login credentials", "E-posta veya şifre hatalı."),
        ("unknown_code", "Something unexpected", "Giriş sırasında bir hata oluştu."),
    ],
)
def test_login_errors_are_shown_in_turkish(frontend_url, code, message, expected):
    stub = (
        "window.supabase = {createClient: () => ({auth: {"
        "onAuthStateChange: () => {},"
        "signInWithPassword: async () => ({error: {name: 'AuthApiError', status: 400,"
        f"code: '{code}', message: '{message}'}}}})}}}})}};"
    )
    with sync_playwright() as p:
        with p.chromium.launch() as browser:
            page = browser.new_context(service_workers="block").new_page()
            page.route(lambda u: not u.startswith("http://127.0.0.1"), lambda r: r.abort())
            page.route("**/cdn.jsdelivr.net/**", lambda r: r.fulfill(body=stub, content_type="application/javascript"))
            page.goto(f"{frontend_url}/login.html")
            page.fill("#loginEmail", "a@example.com")
            page.fill("#loginPassword", "secret123")
            page.click("#loginSubmit")
            page.locator("#authAlert.show").wait_for()
            assert page.inner_text("#authAlert") == expected


@pytest.mark.parametrize(
    "session,latest,expected,form_visible",
    [
        ("null", "[]", "giriş yapın", False),
        ("{user: {id: 'u1'}}", "[]", "onaylandıktan sonra", True),
        ("{user: {id: 'u1'}}", "[{org_name: 'Rota', status: 'pending'}]", "onay bekliyor", False),
        ("{user: {id: 'u1'}}", "[{org_name: 'Rota', status: 'rejected'}]", "onaylanmadı", True),
    ],
)
def test_organization_request_page_states(frontend_url, session, latest, expected, form_visible):
    stub = (
        "window.supabase = {createClient: () => ({"
        f"auth: {{getSession: async () => ({{data: {{session: {session}}}}})}},"
        "from: () => ({select: () => ({eq: () => ({limit: async () => ({data: []})})})}),"
        f"rpc: async () => ({{data: {latest}}})}})}};"
    )
    with sync_playwright() as p:
        with p.chromium.launch() as browser:
            page = browser.new_context(service_workers="block").new_page()
            page.route(lambda u: not u.startswith("http://127.0.0.1"), lambda r: r.abort())
            page.route("**/cdn.jsdelivr.net/**", lambda r: r.fulfill(body=stub, content_type="application/javascript"))
            page.goto(f"{frontend_url}/kurum-basvuru.html")
            page.get_by_text(expected).wait_for()
            assert page.locator("#requestForm").is_visible() == form_visible


def test_invite_token_leaves_address_bar_and_survives_login(frontend_url):
    token = "a" * 64
    stub = "window.supabase = {createClient: () => ({auth: {getSession: async () => ({data: {session: null}})}})};"
    with sync_playwright() as p:
        with p.chromium.launch() as browser:
            page = browser.new_context(service_workers="block").new_page()
            page.route(lambda u: not u.startswith("http://127.0.0.1"), lambda r: r.abort())
            page.route("**/cdn.jsdelivr.net/**", lambda r: r.fulfill(body=stub, content_type="application/javascript"))
            page.goto(f"{frontend_url}/davet.html#davet={token}")
            page.get_by_text("davet edilen e-posta").wait_for()
            assert token not in page.url
            assert page.evaluate("sessionStorage.getItem('adimplan_invite')") == token
            assert page.evaluate("sessionStorage.getItem('adimplan_next')") == "davet.html"
