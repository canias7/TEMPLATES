"""Drive the real index.html / app.js in a browser with a stubbed Supabase."""

import pathlib
import sys

from playwright.sync_api import sync_playwright

APP = pathlib.Path("/home/user/TEMPLATES/teacher-grade-platform")
MOCK = pathlib.Path(__file__).with_name("mock-supabase.js").read_text()
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"

failures = []


def check(label, got, want):
    ok = got == want
    print(("  PASS  " if ok else "  FAIL  ") + label + f"   got={got!r} want={want!r}")
    if not ok:
        failures.append(label)


with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
    page = browser.new_page()
    page.on("pageerror", lambda e: failures.append("JS error: " + str(e)))

    # serve the CDN supabase library from our stub instead
    page.route("**/supabase-js*/**", lambda route: route.fulfill(
        status=200, content_type="application/javascript", body=MOCK))
    page.route("**/supabase.js", lambda route: route.fulfill(
        status=200, content_type="application/javascript", body=MOCK))

    page.goto((APP / "index.html").as_uri())
    page.wait_for_selector("#login-view:not(.hidden)")
    print("\n[1] Login screen shows first, dashboard hidden")
    check("dashboard hidden before login", page.is_hidden("#dashboard-view"), True)

    print("\n[2] Wrong password is rejected")
    page.fill("#email", "teacher.allen@example.com")
    page.fill("#password", "wrong")
    page.click("#login-form button")
    page.wait_for_function("document.getElementById('status').textContent.includes('Login failed')")
    check("still on login screen", page.is_hidden("#dashboard-view"), True)

    print("\n[3] Ms. Allen logs in and sees only her students")
    page.fill("#password", "Teach1234!")
    page.click("#login-form button")
    page.wait_for_selector("#dashboard-view:not(.hidden)")
    names = page.eval_on_selector_all("#rows tr td:first-child",
                                      "els => [...new Set(els.map(e => e.textContent))]")
    check("allen's students", sorted(names), ["Ada Nguyen", "Marcus Webb", "Priya Raman"])
    check("grade rows visible", page.locator("#rows tr").count(), 9)
    check("logged-in email shown", page.inner_text("#who"), "teacher.allen@example.com")
    check("no brooks student leaked",
          any(n in names for n in ["Diego Santos", "Hana Kimura", "Leo Fitzgerald"]), False)

    print("\n[4] Editing a grade saves it")
    first = page.locator("#rows input[type=number]").first
    first.fill("64")
    page.locator("#rows button[data-save]").first.click()
    page.wait_for_function("document.getElementById('status').textContent.includes('Saved')")
    check("stored value changed", page.evaluate(
        "window.__mockState.grades.find(g => g.score === 64) !== undefined"), True)

    print("\n[5] Rejects an out-of-range grade")
    first.fill("500")
    page.locator("#rows button[data-save]").first.click()
    page.wait_for_function("document.getElementById('status').textContent.includes('between 0 and 100')")
    check("500 not stored", page.evaluate(
        "window.__mockState.grades.some(g => g.score === 500)"), False)

    print("\n[6] Logout returns to the login screen")
    page.click("#logout")
    page.wait_for_selector("#login-view:not(.hidden)")
    check("dashboard hidden after logout", page.is_hidden("#dashboard-view"), True)
    check("grade rows cleared", page.locator("#rows tr").count(), 0)

    print("\n[7] Mr. Brooks logs in and sees a completely different class")
    page.fill("#email", "teacher.brooks@example.com")
    page.fill("#password", "Teach1234!")
    page.click("#login-form button")
    page.wait_for_selector("#dashboard-view:not(.hidden)")
    names = page.eval_on_selector_all("#rows tr td:first-child",
                                      "els => [...new Set(els.map(e => e.textContent))]")
    check("brooks's students", sorted(names),
          ["Diego Santos", "Hana Kimura", "Leo Fitzgerald"])
    check("no allen student leaked",
          any(n in names for n in ["Ada Nguyen", "Marcus Webb", "Priya Raman"]), False)

    page.screenshot(path=str(pathlib.Path(__file__).with_name("ui-brooks.png")), full_page=True)
    browser.close()

print("\n" + ("ALL UI CHECKS PASSED" if not failures else "FAILURES: " + repr(failures)))
sys.exit(1 if failures else 0)
