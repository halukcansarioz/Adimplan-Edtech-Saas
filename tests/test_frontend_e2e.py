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
                page = context.new_page()
                errors = []
                page.on("pageerror", lambda err, errs=errors: errs.append(str(err)))
                resp = page.goto(f"{frontend_url}/{page_name}", wait_until="load")
                assert resp is not None and resp.status == 200
                assert page.inner_text("body").strip() != ""
                assert errors == []
                context.close()
